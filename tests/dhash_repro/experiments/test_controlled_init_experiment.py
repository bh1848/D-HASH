from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, List, Tuple, cast

from dhash import DHash
from dhash.routing.alternate import ensure_alternate
from dhash_repro.benchmark.collectors import benchmark_cluster
from dhash_repro.clients.redis_client import flush_databases, redis_client_for_node
from dhash_repro.config.defaults import NODES, REDIS_PORT, SEED, TTL_SECONDS
from dhash_repro.dataset.loader import load_dataset_workload_base
from dhash_repro.workloads.zipf import generate_zipf_workload


class ControlledInitExperiment:
    def setUp(self) -> None:
        print("[setup] Initializing controlled experiment")
        flush_databases(NODES, flush_async=False)

        ranked_keys, trace_size = load_dataset_workload_base("nasa")
        self.trace_path = "dataset=nasa (resolved by load_dataset_workload_base)"
        self.ranked_keys = ranked_keys
        self.trace_size = trace_size
        self.workload = generate_zipf_workload(ranked_keys, size=trace_size, alpha=1.5)
        print(
            f"[setup] Loaded NASA workload base from {self.trace_path} "
            f"(requests={trace_size}, unique_keys={len(ranked_keys)})"
        )
        print("[setup] Generated Zipf workload (alpha=1.5, seed=1337)")

    def _preload_primary_only(self) -> None:
        print("[preload] Writing primary nodes only")
        write_buckets: Dict[str, List[Any]] = defaultdict(list)

        for key in self.ranked_keys:
            primary = self.sharding.get_node(key, op="write")
            write_buckets[primary].append(key)

        self._write_buckets(write_buckets)

    def _preload_with_alt(self) -> None:
        print("[preload] Writing primary and alternate nodes")
        write_buckets: Dict[str, List[Any]] = defaultdict(list)

        for key in self.ranked_keys:
            primary = self.sharding.get_node(key, op="write")
            write_buckets[primary].append(key)

            rich_sharding = cast(Any, self.sharding)
            ensure_alternate(
                key,
                rich_sharding.alt,
                rich_sharding.nodes,
                getattr(rich_sharding.ch, "sorted_keys", []),
                getattr(rich_sharding.ch, "ring", {}),
                getattr(rich_sharding, "_h", hash),
                primary,
            )
            alt = cast(Dict[Any, str], rich_sharding.alt).get(key)
            if alt and alt != primary:
                write_buckets[alt].append(key)

        self._write_buckets(write_buckets)

    def _run_benchmark(self) -> Tuple[float, float, float, float]:
        print("[benchmark] Running benchmark_cluster with pipeline_size=200")
        metrics = benchmark_cluster(self.workload, self.sharding, pipeline_size=200)
        return (
            float(metrics["throughput_ops_s"]),
            float(metrics["avg_ms"]),
            float(metrics["p95_ms"]),
            float(metrics["p99_ms"]),
        )

    def _count_nils(self) -> Tuple[int, int]:
        print("[nil-check] Counting nil responses across workload reads")
        nil_sharding = DHash(NODES, hot_key_threshold=300, window_size=200)
        read_buckets: Dict[str, List[Any]] = defaultdict(list)
        for key in self.workload:
            read_buckets[nil_sharding.get_node(key, op="read")].append(key)

        nil_count = 0
        total = 0

        for node, node_keys in read_buckets.items():
            pipe = redis_client_for_node(node).pipeline()
            for key in node_keys:
                pipe.get(str(key))
            responses = pipe.execute()
            nil_count += sum(1 for response in responses if response is None)
            total += len(responses)

        return nil_count, total

    def run(self) -> None:
        self.setUp()
        results: Dict[str, Tuple[float, float, float, float]] = {}
        nil_results: Dict[str, Tuple[int, int]] = {}

        conditions = [
            ("primary_only", self._preload_primary_only),
            ("with_alt", self._preload_with_alt),
        ]

        for label, preload in conditions:
            print(f"[run] Starting condition: {label}")
            self.sharding = DHash(NODES, hot_key_threshold=300, window_size=200)
            flush_databases(NODES, flush_async=False)
            preload()

            nil_results[label] = self._count_nils()
            results[label] = self._run_benchmark()
            print(f"[run] Finished condition: {label}")

        primary_only = results["primary_only"]
        with_alt = results["with_alt"]
        delta = tuple(after - before for before, after in zip(primary_only, with_alt))

        print("Controlled D-HASH Initialization Experiment")
        print(f"Trace: {self.trace_path}")
        print(f"Seed: {SEED} | Redis port: {REDIS_PORT} | TTL: {TTL_SECONDS}s")
        print()
        print(f"{'Metric':<18}{'primary_only':>16}{'with_alt':>16}{'delta':>16}")
        print("-" * 66)
        rows = [
            ("throughput_ops_s", primary_only[0], with_alt[0], delta[0]),
            ("avg_ms", primary_only[1], with_alt[1], delta[1]),
            ("p95_ms", primary_only[2], with_alt[2], delta[2]),
            ("p99_ms", primary_only[3], with_alt[3], delta[3]),
        ]
        for label, before, after, diff in rows:
            print(f"{label:<18}{before:>16.3f}{after:>16.3f}{diff:>16.3f}")

        primary_nil_count, primary_total = nil_results["primary_only"]
        with_alt_nil_count, with_alt_total = nil_results["with_alt"]
        primary_nil_rate = (primary_nil_count / primary_total * 100.0) if primary_total else 0.0
        with_alt_nil_rate = (with_alt_nil_count / with_alt_total * 100.0) if with_alt_total else 0.0

        print()
        print(f"{'Nil Metric':<18}{'primary_only':>16}{'with_alt':>16}")
        print("-" * 50)
        print(f"{'nil_count':<18}{primary_nil_count:>16}{with_alt_nil_count:>16}")
        print(f"{'total':<18}{primary_total:>16}{with_alt_total:>16}")
        print(f"{'nil_rate (%)':<18}{primary_nil_rate:>16.3f}{with_alt_nil_rate:>16.3f}")

    @staticmethod
    def _write_buckets(write_buckets: Dict[str, List[Any]]) -> None:
        payload = b'{"preload":1}'
        for node, node_keys in write_buckets.items():
            pipe = redis_client_for_node(node).pipeline()
            for key in node_keys:
                pipe.set(str(key), payload, ex=TTL_SECONDS)
            pipe.execute()


if __name__ == "__main__":
    ControlledInitExperiment().run()
