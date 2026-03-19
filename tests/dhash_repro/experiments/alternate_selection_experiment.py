from __future__ import annotations

from bisect import bisect
from collections import defaultdict
from typing import Any, TypedDict, cast

from numpy.random import default_rng

from dhash.routing.guard import check_guard_phase
from dhash.routing.router import DHash
from dhash.routing.window import select_window_route
from dhash_repro.benchmark.collectors import load_stddev
from dhash_repro.config.defaults import NODES
from dhash_repro.dataset.loader import load_dataset_workload_base
from dhash_repro.workloads import zipf as zipf_module
from dhash_repro.workloads.zipf import generate_zipf_workload


class RouterMetrics(TypedDict):
    load_stddev: float
    node_load: dict[str, int]


class VirtualNodeAlternateDHash(DHash):  # type: ignore[misc]
    def _ensure_virtual_alternate(self, key: Any, primary: str) -> None:
        if key in self.alt:
            return

        ring_keys = getattr(self.ch, "sorted_keys", [])
        ring_map = getattr(self.ch, "ring", {})
        if not ring_keys or not ring_map or len(self.nodes) <= 1:
            self.alt[key] = primary
            return

        hk = self._h(key)
        i = bisect(ring_keys, hk) % len(ring_keys)
        stride = 1 + (self._h(f"{key}|alt") % (len(self.nodes) - 1))

        count = 0
        j = i

        for _ in range(len(ring_keys)):
            j = (j + 1) % len(ring_keys)
            cand = ring_map[ring_keys[j]]
            if cand == primary:
                continue
            count += 1
            if count == stride:
                self.alt[key] = cand
                return

        self.alt[key] = primary

    def get_node(self, key: Any, op: str = "read") -> str:
        self._sync_membership_if_needed()

        if op == "write":
            return cast(str, self._primary_safe(key))

        cnt = self.reads.get(key, 0) + 1
        self.reads[key] = cnt

        if cnt < self.T and key not in self.alt:
            return cast(str, self._primary_safe(key))

        primary = self._primary_safe(key)
        self._ensure_virtual_alternate(key, primary)

        if check_guard_phase(cnt, self.T, self.W):
            return cast(str, primary)

        return cast(str, select_window_route(cnt, self.T, self.W, primary, self.alt[key]))


class AlternateSelectionExperiment:
    def __init__(
        self,
        nodes: list[str],
        keys: list[str],
        alpha: float,
        T: int,
        W: int,
        seed: int,
    ) -> None:
        self.nodes = list(nodes)
        self.keys = list(keys)
        self.alpha = alpha
        self.T = T
        self.W = W
        self.seed = seed
        self.results: dict[str, RouterMetrics] | None = None

    def _build_virtual_node_router(self) -> DHash:
        return VirtualNodeAlternateDHash(
            self.nodes,
            hot_key_threshold=self.T,
            window_size=self.W,
            replicas=100,
        )

    def _build_physical_node_router(self) -> DHash:
        return DHash(
            self.nodes,
            hot_key_threshold=self.T,
            window_size=self.W,
            replicas=100,
        )

    def _compute_load_stddev(
        self, router: DHash, workload: list[str]
    ) -> tuple[float, dict[str, int]]:
        node_load: dict[str, int] = defaultdict(int)
        for key in workload:
            node = router.get_node(key, op="read")
            node_load[node] += 1

        normalized = {node: int(node_load.get(node, 0)) for node in self.nodes}
        return float(load_stddev(normalized)), normalized

    def run(self) -> dict[str, RouterMetrics]:
        _, total_requests = load_dataset_workload_base("nasa")
        zipf_module.NP_RNG = default_rng(self.seed)
        workload = generate_zipf_workload(self.keys, size=total_requests, alpha=self.alpha)

        virtual_router = self._build_virtual_node_router()
        physical_router = self._build_physical_node_router()

        virtual_stddev, virtual_load = self._compute_load_stddev(virtual_router, workload)
        physical_stddev, physical_load = self._compute_load_stddev(physical_router, workload)

        self.results = {
            "virtual_node": {
                "load_stddev": virtual_stddev,
                "node_load": virtual_load,
            },
            "physical_node": {
                "load_stddev": physical_stddev,
                "node_load": physical_load,
            },
        }
        return self.results

    def print_results(self) -> None:
        results = self.results if self.results is not None else self.run()
        virtual = results["virtual_node"]
        physical = results["physical_node"]

        virtual_stddev = virtual["load_stddev"]
        physical_stddev = physical["load_stddev"]
        diff = virtual_stddev - physical_stddev
        diff_pct = (diff / physical_stddev * 100.0) if physical_stddev > 0 else 0.0

        virtual_load = virtual["node_load"]
        physical_load = physical["node_load"]

        print("Condition             Load Stddev")
        print("-------------------------------------")
        print(f"{'Virtual Node':<21}{virtual_stddev:>12,.3f}")
        print(f"{'Physical Node':<21}{physical_stddev:>12,.3f}")
        print(f"{'Diff':<21}{diff:>12,.3f} ({diff_pct:.1f}%)")
        print()
        print("Node Load Distribution:")
        print(f"{'':<13}{'redis-1':>9}{'redis-2':>9}{'redis-3':>9}{'redis-4':>9}{'redis-5':>9}")
        print(
            f"{'Virtual':<13}"
            f"{virtual_load.get('redis-1', 0):>9,}"
            f"{virtual_load.get('redis-2', 0):>9,}"
            f"{virtual_load.get('redis-3', 0):>9,}"
            f"{virtual_load.get('redis-4', 0):>9,}"
            f"{virtual_load.get('redis-5', 0):>9,}"
        )
        print(
            f"{'Physical':<13}"
            f"{physical_load.get('redis-1', 0):>9,}"
            f"{physical_load.get('redis-2', 0):>9,}"
            f"{physical_load.get('redis-3', 0):>9,}"
            f"{physical_load.get('redis-4', 0):>9,}"
            f"{physical_load.get('redis-5', 0):>9,}"
        )


if __name__ == "__main__":
    ranked_keys, _ = load_dataset_workload_base("nasa")
    experiment = AlternateSelectionExperiment(
        nodes=NODES,
        keys=ranked_keys,
        alpha=1.5,
        T=300,
        W=200,
        seed=1337,
    )
    experiment.print_results()
