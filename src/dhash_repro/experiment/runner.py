import logging
import os
from typing import Any, Dict, List

from dhash_repro.config.defaults import (
    ABLAT_THRESHOLDS,
    DATASET_DEFAULTS,
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


def run_experiments(mode: str, alpha: float, repeats: int) -> None:
    os.makedirs("persistence", exist_ok=True)

    dataset = resolve_dataset()
    cfg = DATASET_DEFAULTS[dataset]
    ranked_keys, trace_size = load_dataset_workload_base(dataset)

    optimal_B = int(cfg["B"])
    optimal_W = int(cfg["W"])
    optimal_T = int(cfg["T"])
    sweep_rho = float(cfg["rho"])

    if mode in ("pipeline", "all"):
        results: List[Dict[str, Any]] = []
        for B in PIPELINE_SWEEP:
            for rep in range(repeats):
                reset_np_rng(SEED + rep)
                kz = generate_zipf_workload(ranked_keys, size=trace_size, alpha=alpha)
                for m in resolve_algorithms("pipeline", "auto"):
                    d_p = (
                        {"T": max(30, int(round(sweep_rho * B))), "W": B} if m == "D-HASH" else None
                    )
                    t, avg, p95, p99, s = run_single_mode(
                        kz,
                        m,
                        B,
                        d_p,
                        preload_keys=ranked_keys,
                    )
                    results.append(
                        {
                            "Dataset": dataset,
                            "Mode": m,
                            "Alpha": alpha,
                            "Pipeline": B,
                            "W": B if m == "D-HASH" else None,
                            "T": d_p["T"] if d_p else None,
                            "Thr": t,
                            "Avg": avg,
                            "P95": p95,
                            "P99": p99,
                            "LoadSD": s,
                        }
                    )
        save_to_csv(results, f"persistence/{dataset}_pipeline_sweep.csv")

    if mode in ("zipf", "all"):
        results = []
        for a in ZIPF_ALPHAS:
            for rep in range(repeats):
                reset_np_rng(SEED + rep)
                kz = generate_zipf_workload(ranked_keys, size=trace_size, alpha=a)
                for m in resolve_algorithms("zipf", "auto"):
                    d_p = {"T": optimal_T, "W": optimal_W} if m == "D-HASH" else None
                    t, avg, p95, p99, s = run_single_mode(
                        kz,
                        m,
                        optimal_B,
                        d_p,
                        preload_keys=ranked_keys,
                    )
                    results.append(
                        {
                            "Dataset": dataset,
                            "Mode": m,
                            "Alpha": a,
                            "Pipeline": optimal_B,
                            "W": optimal_W if m == "D-HASH" else None,
                            "T": optimal_T if m == "D-HASH" else None,
                            "Thr": t,
                            "Avg": avg,
                            "P95": p95,
                            "P99": p99,
                            "LoadSD": s,
                        }
                    )
        save_to_csv(results, f"persistence/{dataset}_zipf_results.csv")

    if mode in ("ablation", "all"):
        results = []
        for T in ABLAT_THRESHOLDS:
            for rep in range(repeats):
                reset_np_rng(SEED + rep)
                kz = generate_zipf_workload(ranked_keys, size=trace_size, alpha=alpha)
                t, avg, p95, p99, s = run_single_mode(
                    kz,
                    "D-HASH",
                    optimal_B,
                    {"T": T, "W": optimal_W},
                    preload_keys=ranked_keys,
                )
                results.append(
                    {
                        "Dataset": dataset,
                        "Alpha": alpha,
                        "Pipeline": optimal_B,
                        "W": optimal_W,
                        "T": T,
                        "Thr": t,
                        "Avg": avg,
                        "P95": p95,
                        "P99": p99,
                        "LoadSD": s,
                    }
                )
        save_to_csv(results, f"persistence/{dataset}_threshold_ablation.csv")

    env_row = runtime_env_metadata(repeats)
    env_row.update(
        {"dataset": dataset, "trace_requests": trace_size, "unique_keys": len(ranked_keys)}
    )
    save_to_csv([env_row], f"persistence/{dataset}_env_metadata.csv")
    logger.info("All experiments finished for dataset=%s.", dataset)
