import logging
import os
from typing import Any, Dict, List, Optional, Tuple

from dhash import ConsistentHashing, DHash, RendezvousHashing, WeightedConsistentHashing
from dhash.config import REPLICAS
from .config.defaults import (
    NODES,
    PIPELINE_SIZE_DEFAULT,
    PIPELINE_SWEEP,
    SEED,
    ZIPF_ALPHAS,
    reset_np_rng,
    runtime_env_metadata,
)
from .workloads.zipf import generate_zipf_workload
from .clients.redis_client import flush_databases, warmup_cluster
from .benchmark.collectors import benchmark_cluster, load_stddev
from .persistence.writer import save_to_csv

logger = logging.getLogger(__name__)

ALL_MODES: Tuple[str, ...] = ("Consistent Hashing", "Weighted CH", "Rendezvous", "D-HASH")


def resolve_algorithms(stage: str, algos: str) -> List[str]:
    if stage == "microbench" or stage == "pipeline":
        return ["Consistent Hashing", "D-HASH"]
    if stage == "ablation":
        return ["D-HASH"]
    return list(ALL_MODES)


def _mean_std(xs: List[float]) -> Tuple[float, float]:
    if not xs:
        return 0.0, 0.0
    from statistics import mean, stdev

    return float(mean(xs)), float(stdev(xs)) if len(xs) > 1 else 0.0


def run_single_mode(
    keys: List[Any],
    mode_name: str,
    pipeline_size: int,
    dhash_params: Optional[Dict[str, int]] = None,
) -> Tuple[float, float, float, float, float]:
    sh: Any

    if mode_name == "Consistent Hashing":
        sh = ConsistentHashing(NODES, replicas=REPLICAS)
    elif mode_name == "Weighted CH":
        sh = WeightedConsistentHashing(
            NODES, {n: 1.0 + 0.1 * i for i, n in enumerate(NODES)}, base_replicas=REPLICAS
        )
    elif mode_name == "Rendezvous":
        sh = RendezvousHashing(NODES)
    elif mode_name == "D-HASH":
        params = dhash_params or {"T": 50, "W": 1024}
        sh = DHash(NODES, hot_key_threshold=int(params["T"]), window_size=int(params["W"]))
    else:
        raise ValueError(f"Unknown mode: {mode_name}")

    flush_databases(NODES, flush_async=False)
    warmup_cluster(sh, keys)
    metrics = benchmark_cluster(keys, sh, pipeline_size=pipeline_size)

    thr = float(metrics["throughput_ops_s"])
    avg = float(metrics["avg_ms"])
    p95 = float(metrics["p95_ms"])
    p99 = float(metrics["p99_ms"])

    sd = load_stddev(metrics["node_load"])

    logger.info(
        "    -> %s (B=%d): Thr=%.1f, P99=%.3fms, LoadSD=%.0f",
        mode_name,
        pipeline_size,
        thr,
        p99,
        sd,
    )
    return thr, avg, p95, p99, sd


def run_experiments(mode: str, alpha: float, repeats: int) -> None:
    os.makedirs("persistence", exist_ok=True)
    keys = [f"key-{i}" for i in range(100_000)]

    if mode in ("pipeline", "all"):
        results: List[Dict[str, Any]] = []
        for B in PIPELINE_SWEEP:
            for rep in range(repeats):
                reset_np_rng(SEED + rep)
                kz = generate_zipf_workload(keys, size=len(keys), alpha=1.5)
                for m in resolve_algorithms("pipeline", "auto"):
                    d_p = {"T": max(30, B), "W": B} if m == "D-HASH" else None
                    t, _, _, _, s = run_single_mode(kz, m, B, d_p)
                    results.append({"Mode": m, "Pipeline": B, "Thr": t, "LoadSD": s})
        save_to_csv(results, "persistence/pipeline_sweep.csv")

    if mode in ("zipf", "all"):
        results = []
        for a in ZIPF_ALPHAS:
            for rep in range(repeats):
                reset_np_rng(SEED + rep)
                kz = generate_zipf_workload(keys, size=len(keys), alpha=a)
                for m in resolve_algorithms("zipf", "auto"):
                    d_p = (
                        {"T": PIPELINE_SIZE_DEFAULT, "W": PIPELINE_SIZE_DEFAULT}
                        if m == "D-HASH"
                        else None
                    )
                    t, _, _, _, s = run_single_mode(kz, m, PIPELINE_SIZE_DEFAULT, d_p)
                    results.append({"Mode": m, "Alpha": a, "Thr": t, "LoadSD": s})
        save_to_csv(results, "persistence/zipf_results.csv")

    save_to_csv([runtime_env_metadata(repeats)], "persistence/env_metadata.csv")
    logger.info("All experiments finished.")
