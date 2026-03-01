import logging
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from statistics import stdev
from typing import Any, Dict, List, Tuple
from dhash import weighted_percentile
from ..config.defaults import NODES, PIPELINE_SIZE_DEFAULT, TTL_SECONDS, VALUE_BYTES
from ..clients.redis_client import redis_client_for_node

logger = logging.getLogger(__name__)


def load_stddev(node_load: Dict[str, int]) -> float:
    vals = [node_load.get(n, 0) for n in NODES]
    return stdev(vals) if len(vals) > 1 else 0.0


def _value_payload(value_bytes: int) -> bytes:
    base = b'{"v":0}'
    if value_bytes <= len(base):
        return base[: max(value_bytes, 0)]
    return base + b"x" * (value_bytes - len(base))


def benchmark_cluster(
    keys: List[Any],
    sharding: Any,
    ex_seconds: int = TTL_SECONDS,
    pipeline_size: int = PIPELINE_SIZE_DEFAULT,
    value_bytes: int = VALUE_BYTES,
) -> Dict[str, Any]:
    write_buckets: Dict[str, List[Any]] = defaultdict(list)
    read_buckets: Dict[str, List[Any]] = defaultdict(list)

    for k in keys:
        p_node = sharding.get_node(k, op="write")
        write_buckets[p_node].append(k)
        if hasattr(sharding, "_ensure_alternate"):
            sharding._ensure_alternate(k)
            a_node = sharding.alt.get(k)
            if a_node and a_node != p_node:
                write_buckets[a_node].append(k)
        read_buckets[sharding.get_node(k, op="read")].append(k)

    node_load: Dict[str, int] = {
        n: len(write_buckets.get(n, [])) + len(read_buckets.get(n, [])) for n in NODES
    }

    if sum(node_load.values()) == 0:
        logger.warning("No traffic routed to any node.")
        return {
            "throughput_ops_s": 0.0,
            "avg_ms": 0.0,
            "p95_ms": 0.0,
            "p99_ms": 0.0,
            "node_load": node_load,
        }

    payload = _value_payload(value_bytes)

    def _io_write(item: Tuple[str, List[Any]]) -> Tuple[float, List[Tuple[float, int]]]:
        node, node_keys = item
        cli = redis_client_for_node(node)
        total_time = 0.0
        samples: List[Tuple[float, int]] = []
        for i in range(0, len(node_keys), pipeline_size):
            chunk = node_keys[i : i + pipeline_size]
            pipe = cli.pipeline()
            for k in chunk:
                pipe.set(str(k), payload, ex=ex_seconds)
            t0 = time.perf_counter_ns()
            pipe.execute()
            dt = (time.perf_counter_ns() - t0) / 1e9
            total_time += dt
            ops = max(len(chunk), 1)
            samples.append((dt / ops, ops))
        return total_time, samples

    def _io_read(item: Tuple[str, List[Any]]) -> Tuple[float, List[Tuple[float, int]]]:
        node, node_keys = item
        cli = redis_client_for_node(node)
        total_time = 0.0
        samples: List[Tuple[float, int]] = []
        for i in range(0, len(node_keys), pipeline_size):
            chunk = node_keys[i : i + pipeline_size]
            pipe = cli.pipeline()
            for k in chunk:
                pipe.get(str(k))
            t0 = time.perf_counter_ns()
            _ = pipe.execute()
            dt = (time.perf_counter_ns() - t0) / 1e9
            total_time += dt
            ops = max(len(chunk), 1)
            samples.append((dt / ops, ops))
        return total_time, samples

    logger.info(
        "[Bench] Workload: %d Write buckets, %d Read buckets (Pipeline B=%d)",
        len(write_buckets),
        len(read_buckets),
        pipeline_size,
    )

    write_node_totals: List[float] = []
    read_node_totals: List[float] = []
    write_all_samples: List[Tuple[float, int]] = []
    read_all_samples: List[Tuple[float, int]] = []

    with ThreadPoolExecutor(max_workers=max(1, len(write_buckets))) as ex:
        for total, samples in ex.map(_io_write, write_buckets.items()):
            write_node_totals.append(total)
            write_all_samples.extend(samples)

    with ThreadPoolExecutor(max_workers=max(1, len(read_buckets))) as ex:
        for total, samples in ex.map(_io_read, read_buckets.items()):
            read_node_totals.append(total)
            read_all_samples.extend(samples)

    write_ops = sum(len(v) for v in write_buckets.values())
    read_ops = sum(len(v) for v in read_buckets.values())
    total_ops = write_ops + read_ops

    write_wall = max(write_node_totals) if write_node_totals else 0.0
    read_wall = max(read_node_totals) if read_node_totals else 0.0
    cluster_wall = write_wall + read_wall

    throughput = (total_ops / cluster_wall) if cluster_wall > 0 else 0.0

    def _wavg(samples: List[Tuple[float, int]]) -> float:
        wsum = sum(w for _, w in samples)
        if wsum == 0:
            return 0.0
        return sum(v * w for v, w in samples) / wsum

    write_avg_ms = _wavg(write_all_samples) * 1000.0
    read_avg_ms = _wavg(read_all_samples) * 1000.0
    combined_samples = write_all_samples + read_all_samples
    avg_ms = _wavg(combined_samples) * 1000.0

    p95_ms = weighted_percentile(combined_samples, 0.95) * 1000.0
    p99_ms = weighted_percentile(combined_samples, 0.99) * 1000.0
    write_p95_ms = weighted_percentile(write_all_samples, 0.95) * 1000.0
    write_p99_ms = weighted_percentile(write_all_samples, 0.99) * 1000.0
    read_p95_ms = weighted_percentile(read_all_samples, 0.95) * 1000.0
    read_p99_ms = weighted_percentile(read_all_samples, 0.99) * 1000.0

    return {
        "throughput_ops_s": float(throughput),
        "avg_ms": float(avg_ms),
        "p95_ms": float(p95_ms),
        "p99_ms": float(p99_ms),
        "write_avg_ms": float(write_avg_ms),
        "write_p95_ms": float(write_p95_ms),
        "write_p99_ms": float(write_p99_ms),
        "read_avg_ms": float(read_avg_ms),
        "read_p95_ms": float(read_p95_ms),
        "read_p99_ms": float(read_p99_ms),
        "node_load": {n: int(node_load.get(n, 0)) for n in NODES},
    }
