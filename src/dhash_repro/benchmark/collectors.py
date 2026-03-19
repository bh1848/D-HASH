import logging
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from statistics import stdev
from typing import Any, Dict, List, Optional, Tuple

from dhash.stats import weighted_percentile

from ..typing import Sharding
from ..clients.redis_client import redis_client_for_node
from ..config.defaults import NODES, PIPELINE_SIZE_DEFAULT, TTL_SECONDS, VALUE_BYTES

logger = logging.getLogger(__name__)


def load_stddev(node_load: Dict[str, int]) -> float:
    vals = [node_load.get(n, 0) for n in NODES]
    return stdev(vals) if len(vals) > 1 else 0.0


def _value_payload(value_bytes: int) -> bytes:
    base = b'{"v":0}'
    if value_bytes <= len(base):
        return base[: max(value_bytes, 0)]
    return base + b"x" * (value_bytes - len(base))


def _build_io_buckets(
    keys: List[Any],
    sharding: Sharding,
) -> Tuple[Dict[str, List[Any]], Dict[str, List[Any]]]:
    write_buckets: Dict[str, List[Any]] = defaultdict(list)
    read_buckets: Dict[str, List[Any]] = defaultdict(list)

    for key in keys:
        primary_node = sharding.get_node(key, op="write")
        write_buckets[primary_node].append(key)
        read_buckets[sharding.get_node(key, op="read")].append(key)

    return write_buckets, read_buckets


def _run_node_batches(
    node: str,
    node_keys: List[Any],
    *,
    pipeline_size: int,
    payload: Optional[bytes],
    ex_seconds: int,
) -> Tuple[float, List[Tuple[float, int]]]:
    cli = redis_client_for_node(node)
    total_time = 0.0
    samples: List[Tuple[float, int]] = []

    for i in range(0, len(node_keys), pipeline_size):
        chunk = node_keys[i : i + pipeline_size]
        pipe = cli.pipeline()
        for key in chunk:
            if payload is None:
                pipe.get(str(key))
            else:
                pipe.set(str(key), payload, ex=ex_seconds)
        t0 = time.perf_counter_ns()
        _ = pipe.execute()
        dt = (time.perf_counter_ns() - t0) / 1e9
        total_time += dt
        ops = max(len(chunk), 1)
        samples.append((dt / ops, ops))

    return total_time, samples


def _wavg(samples: List[Tuple[float, int]]) -> float:
    wsum = sum(weight for _, weight in samples)
    return sum(value * weight for value, weight in samples) / wsum if wsum > 0 else 0.0


def benchmark_cluster(
    keys: List[Any],
    sharding: Sharding,
    ex_seconds: int = TTL_SECONDS,
    pipeline_size: int = PIPELINE_SIZE_DEFAULT,
    value_bytes: int = VALUE_BYTES,
) -> Dict[str, Any]:
    write_buckets, read_buckets = _build_io_buckets(keys, sharding)

    node_load: Dict[str, int] = {
        n: len(write_buckets.get(n, [])) + len(read_buckets.get(n, [])) for n in NODES
    }

    if sum(node_load.values()) == 0:
        return {
            "throughput_ops_s": 0.0,
            "avg_ms": 0.0,
            "p95_ms": 0.0,
            "p99_ms": 0.0,
            "write_avg_ms": 0.0,
            "write_p95_ms": 0.0,
            "write_p99_ms": 0.0,
            "read_avg_ms": 0.0,
            "read_p95_ms": 0.0,
            "read_p99_ms": 0.0,
            "node_load": node_load,
        }

    payload = _value_payload(value_bytes)

    def _io_write(item: Tuple[str, List[Any]]) -> Tuple[float, List[Tuple[float, int]]]:
        node, node_keys = item
        return _run_node_batches(
            node,
            node_keys,
            pipeline_size=pipeline_size,
            payload=payload,
            ex_seconds=ex_seconds,
        )

    def _io_read(item: Tuple[str, List[Any]]) -> Tuple[float, List[Tuple[float, int]]]:
        node, node_keys = item
        return _run_node_batches(
            node,
            node_keys,
            pipeline_size=pipeline_size,
            payload=None,
            ex_seconds=ex_seconds,
        )

    write_node_totals, write_all_samples = [], []
    read_node_totals, read_all_samples = [], []

    with ThreadPoolExecutor(max_workers=max(1, len(write_buckets))) as ex:
        for total, samples in ex.map(_io_write, write_buckets.items()):
            write_node_totals.append(total)
            write_all_samples.extend(samples)

    with ThreadPoolExecutor(max_workers=max(1, len(read_buckets))) as ex:
        for total, samples in ex.map(_io_read, read_buckets.items()):
            read_node_totals.append(total)
            read_all_samples.extend(samples)

    cluster_wall = (max(write_node_totals) if write_node_totals else 0.0) + (
        max(read_node_totals) if read_node_totals else 0.0
    )
    total_ops = sum(len(v) for v in write_buckets.values()) + sum(
        len(v) for v in read_buckets.values()
    )
    throughput = (total_ops / cluster_wall) if cluster_wall > 0 else 0.0

    combined_samples = write_all_samples + read_all_samples
    write_avg_ms = _wavg(write_all_samples) * 1000.0
    read_avg_ms = _wavg(read_all_samples) * 1000.0
    return {
        "throughput_ops_s": float(throughput),
        "avg_ms": float(_wavg(combined_samples) * 1000.0),
        "p95_ms": float(weighted_percentile(combined_samples, 0.95) * 1000.0),
        "p99_ms": float(weighted_percentile(combined_samples, 0.99) * 1000.0),
        "write_avg_ms": float(write_avg_ms),
        "write_p95_ms": float(weighted_percentile(write_all_samples, 0.95) * 1000.0),
        "write_p99_ms": float(weighted_percentile(write_all_samples, 0.99) * 1000.0),
        "read_avg_ms": float(read_avg_ms),
        "read_p95_ms": float(weighted_percentile(read_all_samples, 0.95) * 1000.0),
        "read_p99_ms": float(weighted_percentile(read_all_samples, 0.99) * 1000.0),
        "node_load": {n: int(node_load.get(n, 0)) for n in NODES},
    }
