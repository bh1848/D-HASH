import gc
import logging
import os
import random
import time
from statistics import mean, stdev
from typing import Any, Callable, Dict, List, Optional, Tuple

from dhash import ConsistentHashing, DHash, RendezvousHashing, WeightedConsistentHashing
from dhash.config import VIRTUAL_POINTS_PER_NODE
from dhash_repro.config.defaults import (
    ABLAT_THRESHOLDS,
    DATASET_DEFAULTS,
    MICROBENCH_NUM_KEYS,
    MICROBENCH_OPS,
    PIPELINE_SWEEP,
    SEED,
    ZIPF_ALPHAS,
    reset_np_rng,
    runtime_env_metadata,
)
from dhash_repro.dataset.loader import load_dataset_workload_base, resolve_dataset
from dhash_repro.experiment.modes import resolve_algorithms, run_single_mode
from dhash_repro.persistence.writer import save_to_csv
from dhash_repro.workloads.zipf import generate_zipf_workload

logger = logging.getLogger(__name__)
_DATASET_LABELS: Dict[str, str] = {"nasa": "NASA", "ebay": "eBay"}


def _dataset_runtime_params(
    dataset: str,
    *,
    fixed_window: Optional[int],
    dhash_t: Optional[int],
    pipeline_for_zipf: Optional[int],
) -> Dict[str, int]:
    cfg = DATASET_DEFAULTS[dataset]
    optimal_b = int(cfg["B"])
    optimal_w = int(cfg["W"])
    optimal_t = int(cfg["T"])
    zipf_window = fixed_window or optimal_w
    return {
        "optimal_b": optimal_b,
        "optimal_w": optimal_w,
        "optimal_t": optimal_t,
        "zipf_window": zipf_window,
        "zipf_pipeline": pipeline_for_zipf or optimal_b,
        "zipf_threshold": dhash_t if dhash_t is not None else optimal_t,
        "microbench_window": fixed_window or optimal_w,
        "ablation_window": fixed_window or pipeline_for_zipf or optimal_w,
    }


def _mean_std(xs: List[float]) -> Tuple[float, float]:
    if not xs:
        return 0.0, 0.0
    if len(xs) == 1:
        return float(xs[0]), 0.0
    return float(mean(xs)), float(stdev(xs))


def _save_stage_env(dataset: str, stage: str, repeats: int, extra: Dict[str, Any]) -> None:
    row = runtime_env_metadata(repeats)
    row.update(extra)
    save_to_csv([row], f"persistence/{dataset}_{stage}_env_meta.csv")


def _iter_selected_datasets(dataset_filter: Optional[str]) -> List[Tuple[str, str]]:
    if dataset_filter is None:
        dataset_key = resolve_dataset()
        return [(_DATASET_LABELS.get(dataset_key, dataset_key.upper()), dataset_key)]

    normalized = dataset_filter.strip().lower()
    if normalized == "all":
        return [("NASA", "nasa"), ("eBay", "ebay")]
    if normalized in _DATASET_LABELS:
        return [(_DATASET_LABELS[normalized], normalized)]

    raise ValueError("dataset_filter must be one of: ALL, nasa, ebay")


def _stage_common_extra(
    dataset: str,
    dataset_label: str,
    trace_size: int,
    workload_size: int,
) -> Dict[str, Any]:
    return {
        "dataset": dataset,
        "dataset_label": dataset_label,
        "trace_requests": trace_size,
        "workload_size": workload_size,
    }


def _microbench_once_get_node(
    algo: str,
    num_ops: int,
    num_keys: int,
    dhash_params: Optional[Dict[str, int]] = None,
    hot: bool = False,
    rng_seed: int = SEED,
) -> float:
    if algo == "CH":
        sh = ConsistentHashing(
            [f"redis-{i}" for i in range(1, 6)],
            replicas=VIRTUAL_POINTS_PER_NODE,
        )
    elif algo == "D-HASH":
        params = dhash_params or {"T": 50, "W": 1024}
        sh = DHash(
            [f"redis-{i}" for i in range(1, 6)],
            hot_key_threshold=int(params["T"]),
            window_size=int(params["W"]),
        )
    else:
        raise ValueError("algo must be 'CH' or 'D-HASH' for microbench")

    keys = [f"mbkey-{i}" for i in range(num_keys)]
    if algo == "D-HASH" and hot:
        threshold = getattr(sh, "hot_key_threshold", int((dhash_params or {}).get("T", 50)))
        for key in keys:
            for _ in range(threshold + 1):
                _ = sh.get_node(key)

    rng = random.Random(rng_seed)
    key_idx = 0
    start = time.perf_counter_ns()
    for _ in range(num_ops):
        key = keys[key_idx]
        _ = sh.get_node(key)
        key_idx += 1
        if key_idx == num_keys:
            key_idx = 0
            rng.shuffle(keys)
    return float((time.perf_counter_ns() - start) / num_ops)


def run_microbench(dataset: str, repeats: int, window_size: int) -> None:
    rows: List[Dict[str, Any]] = []
    results: List[Tuple[str, str, float]] = []
    cfg = DATASET_DEFAULTS[dataset]
    dhash_params = {"T": int(cfg["T"]), "W": window_size}

    for rep in range(repeats):
        results.append(
            (
                "CH",
                "cold",
                _microbench_once_get_node(
                    "CH", MICROBENCH_OPS, MICROBENCH_NUM_KEYS, rng_seed=SEED + rep
                ),
            )
        )
        results.append(
            (
                "D-HASH",
                "cold",
                _microbench_once_get_node(
                    "D-HASH",
                    MICROBENCH_OPS,
                    MICROBENCH_NUM_KEYS,
                    dhash_params=dhash_params,
                    hot=False,
                    rng_seed=SEED + rep,
                ),
            )
        )
        results.append(
            (
                "D-HASH",
                "hot",
                _microbench_once_get_node(
                    "D-HASH",
                    MICROBENCH_OPS,
                    MICROBENCH_NUM_KEYS,
                    dhash_params=dhash_params,
                    hot=True,
                    rng_seed=SEED + rep,
                ),
            )
        )

    for algo in ["CH", "D-HASH"]:
        phases = ["cold"] if algo == "CH" else ["cold", "hot"]
        for phase in phases:
            vals = [
                value
                for cur_algo, cur_phase, value in results
                if cur_algo == algo and cur_phase == phase
            ]
            avg_ns, std_ns = _mean_std(vals)
            rows.append(
                {
                    "Dataset": dataset,
                    "Stage": "Microbench",
                    "Algorithm": algo,
                    "Phase": phase,
                    "ns/op (avg)": avg_ns,
                    "ns/op (std)": std_ns,
                    "Promotions (sum)": 0,
                    "Lock Acquires (sum)": 0,
                    "Repeats": repeats,
                    "Ops per Repeat": MICROBENCH_OPS,
                    "Keys": MICROBENCH_NUM_KEYS,
                    "DHash.T": dhash_params["T"] if algo == "D-HASH" else "",
                    "DHash.R": 2 if algo == "D-HASH" else "",
                    "DHash.W": dhash_params["W"] if algo == "D-HASH" else "",
                }
            )

    save_to_csv(rows, f"persistence/{dataset}_microbench_ns.csv")
    _save_stage_env(
        dataset,
        "microbench",
        repeats,
        {
            "dataset": dataset,
            "ops_per_repeat": MICROBENCH_OPS,
            "keys": MICROBENCH_NUM_KEYS,
        },
    )


def compute_redistribution_rate(
    nodes_before: List[str],
    nodes_after: List[str],
    keys: List[Any],
    ctor: Callable[[List[str]], Any],
) -> float:
    sh_before = ctor(nodes_before)
    sh_after = ctor(nodes_after)
    moved = sum(1 for key in keys if sh_before.get_node(key) != sh_after.get_node(key))
    return moved / max(1, len(keys))


def run_redistribution_report(dataset: str, keys: List[Any], repeats: int) -> None:
    sample_keys = keys[: min(100_000, len(keys))]
    nodes_a = [f"redis-{i}" for i in range(1, 6)]
    nodes_b = [f"redis-{i}" for i in range(1, 7)]

    def _ch_ctor(nodes: List[str]) -> Any:
        return ConsistentHashing(nodes, replicas=VIRTUAL_POINTS_PER_NODE)

    def _wch_ctor(nodes: List[str]) -> Any:
        weights = {node: 1.0 + 0.1 * idx for idx, node in enumerate(nodes)}
        return WeightedConsistentHashing(
            nodes, weights=weights, base_replicas=VIRTUAL_POINTS_PER_NODE
        )

    def _rv_ctor(nodes: List[str]) -> Any:
        return RendezvousHashing(nodes)

    rows: List[Dict[str, Any]] = []
    for algo, ctor in (
        ("CH", _ch_ctor),
        ("WCH", _wch_ctor),
        ("Rendezvous", _rv_ctor),
    ):
        rows.append(
            {
                "Algorithm": algo,
                "Event": "5->6",
                "Move (%)": compute_redistribution_rate(nodes_a, nodes_b, sample_keys, ctor) * 100,
            }
        )
        rows.append(
            {
                "Algorithm": algo,
                "Event": "6->5",
                "Move (%)": compute_redistribution_rate(nodes_b, nodes_a, sample_keys, ctor) * 100,
            }
        )

    save_to_csv(rows, f"persistence/{dataset}_redistribution.csv")
    _save_stage_env(
        dataset,
        "redistribution",
        repeats,
        {
            "dataset": dataset,
            "sample_keys": len(sample_keys),
        },
    )


def _run_pipeline_stage(
    dataset: str,
    dataset_label: str,
    keys: List[Any],
    trace_size: int,
    repeats: int,
    algos: str,
    algos_list: str,
) -> None:
    results: List[Dict[str, Any]] = []
    for batch_size in PIPELINE_SWEEP:
        for rep in range(repeats):
            gc.collect()
            reset_np_rng(SEED + rep)
            workload = generate_zipf_workload(keys, size=len(keys), alpha=1.5)
            for algo in resolve_algorithms("pipeline", algos, algos_list):
                params = {"T": max(30, batch_size), "W": batch_size} if algo == "D-HASH" else None
                thr, avg, p95, p99, sd = run_single_mode(
                    workload,
                    algo,
                    batch_size,
                    params,
                )
                results.append(
                    {
                        "Dataset": dataset,
                        "DatasetLabel": dataset_label,
                        "Mode": algo,
                        "Alpha": 1.5,
                        "Pipeline": batch_size,
                        "W": batch_size if algo == "D-HASH" else None,
                        "T": params["T"] if params else None,
                        "Thr": thr,
                        "Avg": avg,
                        "P95": p95,
                        "P99": p99,
                        "LoadSD": sd,
                    }
                )
    save_to_csv(results, f"persistence/{dataset}_pipeline_sweep.csv")
    _save_stage_env(
        dataset,
        "pipeline",
        repeats,
        _stage_common_extra(dataset, dataset_label, trace_size, len(keys)),
    )


def _run_zipf_stage(
    dataset: str,
    dataset_label: str,
    keys: List[Any],
    trace_size: int,
    repeats: int,
    algos: str,
    algos_list: str,
    *,
    alpha_values: List[float],
    zipf_window: int,
    zipf_pipeline: int,
    zipf_threshold: int,
) -> None:
    results: List[Dict[str, Any]] = []
    for cur_alpha in alpha_values:
        for rep in range(repeats):
            gc.collect()
            reset_np_rng(SEED + rep)
            workload = generate_zipf_workload(keys, size=len(keys), alpha=cur_alpha)
            for algo in resolve_algorithms("zipf", algos, algos_list):
                params = {"T": zipf_threshold, "W": zipf_window} if algo == "D-HASH" else None
                thr, avg, p95, p99, sd = run_single_mode(
                    workload,
                    algo,
                    zipf_pipeline,
                    params,
                )
                results.append(
                    {
                        "Dataset": dataset,
                        "DatasetLabel": dataset_label,
                        "Mode": algo,
                        "Alpha": cur_alpha,
                        "Pipeline": zipf_pipeline,
                        "W": zipf_window if algo == "D-HASH" else None,
                        "T": zipf_threshold if algo == "D-HASH" else None,
                        "Thr": thr,
                        "Avg": avg,
                        "P95": p95,
                        "P99": p99,
                        "LoadSD": sd,
                    }
                )
    save_to_csv(results, f"persistence/{dataset}_zipf_results.csv")
    extra = _stage_common_extra(dataset, dataset_label, trace_size, len(keys))
    extra.update(
        {
            "zipf_window": zipf_window,
            "zipf_pipeline": zipf_pipeline,
            "zipf_threshold": zipf_threshold,
        }
    )
    _save_stage_env(dataset, "zipf", repeats, extra)


def _run_ablation_stage(
    dataset: str,
    dataset_label: str,
    keys: List[Any],
    trace_size: int,
    repeats: int,
    alpha: float,
    *,
    ablation_window: int,
) -> None:
    results: List[Dict[str, Any]] = []
    for threshold in ABLAT_THRESHOLDS:
        for rep in range(repeats):
            gc.collect()
            reset_np_rng(SEED + rep)
            workload = generate_zipf_workload(keys, size=len(keys), alpha=alpha)
            thr, avg, p95, p99, sd = run_single_mode(
                workload,
                "D-HASH",
                ablation_window,
                {"T": threshold, "W": ablation_window},
            )
            results.append(
                {
                    "Dataset": dataset,
                    "DatasetLabel": dataset_label,
                    "Alpha": alpha,
                    "Pipeline": ablation_window,
                    "W": ablation_window,
                    "T": threshold,
                    "Thr": thr,
                    "Avg": avg,
                    "P95": p95,
                    "P99": p99,
                    "LoadSD": sd,
                }
            )
    save_to_csv(results, f"persistence/{dataset}_threshold_ablation.csv")
    extra = _stage_common_extra(dataset, dataset_label, trace_size, len(keys))
    extra["ablation_window"] = ablation_window
    _save_stage_env(dataset, "ablation", repeats, extra)


def run_experiments(
    mode: str,
    alpha: float,
    repeats: int,
    dataset_filter: Optional[str] = None,
    fixed_window: Optional[int] = None,
    dhash_t: Optional[int] = None,
    pipeline_for_zipf: Optional[int] = None,
    algos: str = "auto",
    algos_list: str = "",
    zipf_alphas: Optional[List[float]] = None,
) -> None:
    os.makedirs("persistence", exist_ok=True)

    completed_any = False
    for dataset_label, dataset in _iter_selected_datasets(dataset_filter):
        try:
            keys, trace_size = load_dataset_workload_base(dataset)
        except Exception as exc:
            logger.warning("[%s] Dataset load skipped: %s", dataset_label, exc)
            continue

        completed_any = True
        params = _dataset_runtime_params(
            dataset,
            fixed_window=fixed_window,
            dhash_t=dhash_t,
            pipeline_for_zipf=pipeline_for_zipf,
        )

        if mode in ("pipeline", "all"):
            _run_pipeline_stage(
                dataset,
                dataset_label,
                keys,
                trace_size,
                repeats,
                algos,
                algos_list,
            )

        if mode in ("microbench", "all"):
            run_microbench(dataset, repeats, params["microbench_window"])

        if mode in ("zipf", "all"):
            _run_zipf_stage(
                dataset,
                dataset_label,
                keys,
                trace_size,
                repeats,
                algos,
                algos_list,
                alpha_values=zipf_alphas or ZIPF_ALPHAS,
                zipf_window=params["zipf_window"],
                zipf_pipeline=params["zipf_pipeline"],
                zipf_threshold=params["zipf_threshold"],
            )

        if mode in ("ablation", "all"):
            _run_ablation_stage(
                dataset,
                dataset_label,
                keys,
                trace_size,
                repeats,
                alpha,
                ablation_window=params["ablation_window"],
            )

        if mode == "redistrib":
            run_redistribution_report(dataset, keys, repeats)

        save_to_csv(
            [
                {
                    **runtime_env_metadata(repeats),
                    "dataset": dataset,
                    "dataset_label": dataset_label,
                    "trace_requests": trace_size,
                    "workload_size": len(keys),
                }
            ],
            f"persistence/{dataset}_env_metadata.csv",
        )
        logger.info("All experiments finished for dataset=%s.", dataset)

    if not completed_any:
        logger.warning("No datasets were executed for mode=%s.", mode)
