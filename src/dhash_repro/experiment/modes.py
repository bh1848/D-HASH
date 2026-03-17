import logging
from typing import Any, Dict, List, Optional, Tuple

from dhash import ConsistentHashing, DHash, RendezvousHashing, WeightedConsistentHashing
from dhash.config import VIRTUAL_POINTS_PER_NODE

from dhash_repro.benchmark.collectors import benchmark_cluster, load_stddev
from dhash_repro.clients.redis_client import flush_databases, preload_cluster, warmup_cluster
from dhash_repro.config.defaults import NODES
from dhash_repro.typing import Sharding

logger = logging.getLogger(__name__)

ALL_MODES: Tuple[str, ...] = ("Consistent Hashing", "Weighted CH", "Rendezvous", "D-HASH")


def resolve_algorithms(stage: str, algos: str) -> List[str]:
    if stage in ("microbench", "pipeline"):
        return ["Consistent Hashing", "D-HASH"]
    if stage == "ablation":
        return ["D-HASH"]
    return list(ALL_MODES)


def run_single_mode(
    keys: List[Any],
    mode_name: str,
    pipeline_size: int,
    dhash_params: Optional[Dict[str, int]] = None,
    preload_keys: Optional[List[Any]] = None,
) -> Tuple[float, float, float, float, float]:
    sh: Sharding

    if mode_name == "Consistent Hashing":
        sh = ConsistentHashing(NODES, replicas=VIRTUAL_POINTS_PER_NODE)
    elif mode_name == "Weighted CH":
        sh = WeightedConsistentHashing(
            NODES,
            {n: 1.0 + 0.1 * i for i, n in enumerate(NODES)},
            base_replicas=VIRTUAL_POINTS_PER_NODE,
        )
    elif mode_name == "Rendezvous":
        sh = RendezvousHashing(NODES)
    elif mode_name == "D-HASH":
        params = dhash_params or {"T": 300, "W": pipeline_size}
        sh = DHash(NODES, hot_key_threshold=int(params["T"]), window_size=int(params["W"]))
    else:
        raise ValueError(f"Unknown mode: {mode_name}")

    warm_keys = preload_keys if preload_keys is not None else list(dict.fromkeys(keys))

    flush_databases(NODES, flush_async=False)

    preload_cluster(sh, warm_keys)
    warmup_cluster(sh, warm_keys)

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
