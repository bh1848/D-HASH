from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from benchmarks.workloads import Workload, build_zipf_workload, iter_batches, materialize_ops
from dhash.hashing import (
    ConsistentHashing,
    RendezvousHashing,
    WeightedConsistentHashing,
)
from dhash.measure.metrics import load_stddev
from dhash.measure.percentile import weighted_percentile
from dhash.routing import DHash
from dhash.utils.io import write_csv, write_json
from dhash.utils.time import now_ns


@dataclass(frozen=True)
class RunConfig:
    nodes: list[str]
    threshold: int
    window: int
    replicas: int

    # workload sweep
    num_ops: int
    num_keys: int
    alphas: list[float]
    read_ratio: float
    pipelines: list[int]
    seed: int
    repeats: int

    # algo sweep
    algos: list[str]


def _default_nodes(n: int) -> list[str]:
    return [f"redis-{i}" for i in range(1, n + 1)]


def _parse_algos(raw: str) -> list[str]:
    raw = raw.strip().lower()
    if raw == "all":
        return ["ch", "wch", "hrw", "dhash"]
    # allow comma-separated list
    parts = [x.strip().lower() for x in raw.split(",") if x.strip()]
    # keep order, de-dup
    seen = set()
    out: list[str] = []
    for p in parts:
        if p not in seen:
            seen.add(p)
            out.append(p)
    return out


def _make_router(algo: str, cfg: RunConfig):
    """
    Create router instance for a given algorithm.
    """
    algo = algo.lower()

    if algo == "dhash":
        return DHash(
            nodes=cfg.nodes,
            hot_key_threshold=cfg.threshold,
            window_size=cfg.window,
            replicas=cfg.replicas,
        )

    if algo == "ch":
        return ConsistentHashing(cfg.nodes, replicas=cfg.replicas)

    if algo == "wch":
        # default: uniform weights (capacity-aware weighting can be added later)
        weights = {n: 1.0 for n in cfg.nodes}
        return WeightedConsistentHashing(cfg.nodes, weights=weights, base_replicas=cfg.replicas)

    if algo == "hrw":
        return RendezvousHashing(cfg.nodes)

    raise ValueError(f"Unknown algo: {algo}")


def _load_stats(node_load: dict[str, int], nodes: list[str]) -> dict[str, float]:
    vals = [float(node_load.get(n, 0)) for n in nodes]
    if not vals:
        return {"load_mean": 0.0, "load_max": 0.0, "load_min": 0.0}
    return {
        "load_mean": float(sum(vals) / len(vals)),
        "load_max": float(max(vals)),
        "load_min": float(min(vals)),
    }


def _run_one_workload(
    *,
    w: Workload,
    cfg: RunConfig,
    algo: str,
) -> dict[str, Any]:
    """
    Execute one workload for one algorithm.

    Measurement:
    - Each pipeline batch is timed (ns)
    - Convert to avg latency per op in that batch: dt / batch_size
    - Weighted percentiles computed with weight=batch_size
    """
    keys, ops = materialize_ops(w)

    router = _make_router(algo, cfg)

    batch_samples: list[tuple[float, int]] = []
    node_load: dict[str, int] = {n: 0 for n in cfg.nodes}

    total_ops = 0
    total_ns = 0

    for b_keys, b_ops in iter_batches(keys, ops, w.pipeline):
        b0 = now_ns()
        for k, op in zip(b_keys, b_ops, strict=False):
            node = router.get_node(k, op=op)
            node_load[node] = node_load.get(node, 0) + 1
        b1 = now_ns()

        bs = len(b_keys)
        dt = b1 - b0

        total_ops += bs
        total_ns += dt

        avg = float(dt) / float(bs)  # ns per op (batch average)
        batch_samples.append((avg, bs))

    p50 = weighted_percentile(batch_samples, 0.50)
    p95 = weighted_percentile(batch_samples, 0.95)
    p99 = weighted_percentile(batch_samples, 0.99)

    std = float(load_stddev(node_load))
    mean_latency = float(total_ns) / float(max(1, total_ops))

    stats = _load_stats(node_load, cfg.nodes)

    return {
        "algo": algo,
        "workload": asdict(w),
        "total_ops": total_ops,
        "total_ns": total_ns,
        "avg_latency_ns": mean_latency,
        "p50_latency_ns": p50,
        "p95_latency_ns": p95,
        "p99_latency_ns": p99,
        "load_stddev": std,
        "load_mean": stats["load_mean"],
        "load_max": stats["load_max"],
        "load_min": stats["load_min"],
        "node_load": node_load,
    }


def _repeat_workload(
    *,
    w: Workload,
    cfg: RunConfig,
    algo: str,
    repeats: int,
) -> dict[str, Any]:
    """
    Repeat one workload multiple times and summarize.
    """
    results = []
    for r in range(repeats):
        # make repeat deterministic but non-identical
        wr = Workload(
            name=f"{w.name}_r{r}",
            kind=w.kind,
            num_ops=w.num_ops,
            num_keys=w.num_keys,
            alpha=w.alpha,
            read_ratio=w.read_ratio,
            pipeline=w.pipeline,
            seed=w.seed + r,
        )
        results.append(_run_one_workload(w=wr, cfg=cfg, algo=algo))

    def _mean(xs: list[float]) -> float:
        return float(sum(xs) / max(1, len(xs)))

    return {
        "algo": algo,
        "workload": asdict(w),
        "repeats": repeats,
        "avg_latency_ns_mean": _mean([x["avg_latency_ns"] for x in results]),
        "p50_latency_ns_mean": _mean([x["p50_latency_ns"] for x in results]),
        "p95_latency_ns_mean": _mean([x["p95_latency_ns"] for x in results]),
        "p99_latency_ns_mean": _mean([x["p99_latency_ns"] for x in results]),
        "load_stddev_mean": _mean([x["load_stddev"] for x in results]),
        "load_mean_mean": _mean([x["load_mean"] for x in results]),
        "load_max_mean": _mean([x["load_max"] for x in results]),
        "load_min_mean": _mean([x["load_min"] for x in results]),
        "runs": results,
    }


def _build_workload_sweep(cfg: RunConfig) -> list[Workload]:
    ws: list[Workload] = []
    for a in cfg.alphas:
        for p in cfg.pipelines:
            ws.append(
                build_zipf_workload(
                    alpha=a,
                    num_ops=cfg.num_ops,
                    num_keys=cfg.num_keys,
                    read_ratio=cfg.read_ratio,
                    pipeline=p,
                    seed=cfg.seed,
                )
            )
    return ws


def _flatten_csv_rows(
    run_id: str, cfg: RunConfig, summaries: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for s in summaries:
        w = s["workload"]
        rows.append(
            {
                "run_id": run_id,
                "algo": s["algo"],
                "kind": w["kind"],
                "name": w["name"],
                "alpha": w["alpha"],
                "num_ops": w["num_ops"],
                "num_keys": w["num_keys"],
                "read_ratio": w["read_ratio"],
                "pipeline": w["pipeline"],
                "seed": w["seed"],
                "threshold": cfg.threshold,
                "window": cfg.window,
                "replicas": cfg.replicas,
                "nodes": ",".join(cfg.nodes),
                "repeats": s["repeats"],
                "avg_latency_ns_mean": s["avg_latency_ns_mean"],
                "p50_latency_ns_mean": s["p50_latency_ns_mean"],
                "p95_latency_ns_mean": s["p95_latency_ns_mean"],
                "p99_latency_ns_mean": s["p99_latency_ns_mean"],
                "load_stddev_mean": s["load_stddev_mean"],
                "load_mean_mean": s["load_mean_mean"],
                "load_max_mean": s["load_max_mean"],
                "load_min_mean": s["load_min_mean"],
            }
        )
    return rows


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="dhash-bench")

    ap.add_argument("--out", default="benchmarks/outputs", help="output directory")
    ap.add_argument("--nodes", type=int, default=5, help="number of nodes")

    ap.add_argument("--threshold", type=int, default=50, help="hot-key threshold T (DHash)")
    ap.add_argument("--window", type=int, default=500, help="routing window W (DHash)")
    ap.add_argument(
        "--replicas", type=int, default=100, help="virtual replicas (CH/WCH/DHash ring)"
    )

    ap.add_argument("--num-ops", type=int, default=200_000)
    ap.add_argument("--num-keys", type=int, default=10_000)
    ap.add_argument("--alphas", default="1.1,1.3,1.5", help="comma-separated zipf alphas")
    ap.add_argument("--read-ratio", type=float, default=0.95)
    ap.add_argument("--pipelines", default="50,100,200,500", help="comma-separated pipeline sizes")
    ap.add_argument("--seed", type=int, default=1337)
    ap.add_argument("--repeats", type=int, default=3)

    ap.add_argument(
        "--algo",
        default="all",
        help="Algorithms: ch,wch,hrw,dhash or comma list, or 'all'",
    )

    ns = ap.parse_args(argv)

    cfg = RunConfig(
        nodes=_default_nodes(int(ns.nodes)),
        threshold=int(ns.threshold),
        window=int(ns.window),
        replicas=int(ns.replicas),
        num_ops=int(ns.num_ops),
        num_keys=int(ns.num_keys),
        alphas=[float(x.strip()) for x in str(ns.alphas).split(",") if x.strip()],
        read_ratio=float(ns.read_ratio),
        pipelines=[int(x.strip()) for x in str(ns.pipelines).split(",") if x.strip()],
        seed=int(ns.seed),
        repeats=max(1, int(ns.repeats)),
        algos=_parse_algos(str(ns.algo)),
    )

    out_dir = Path(ns.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    workloads = _build_workload_sweep(cfg)

    summaries: list[dict[str, Any]] = []
    for algo in cfg.algos:
        for w in workloads:
            summaries.append(_repeat_workload(w=w, cfg=cfg, algo=algo, repeats=cfg.repeats))

    payload = {
        "run_id": run_id,
        "config": asdict(cfg),
        "summaries": summaries,
    }

    json_path = out_dir / f"{run_id}.json"
    csv_path = out_dir / f"{run_id}.csv"

    write_json(json_path, payload)
    write_csv(csv_path, _flatten_csv_rows(run_id, cfg, summaries))

    print(f"[OK] wrote: {json_path}")
    print(f"[OK] wrote: {csv_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
