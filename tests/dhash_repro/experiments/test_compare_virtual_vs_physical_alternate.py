from __future__ import annotations

from bisect import bisect
from collections import Counter
from dataclasses import dataclass
from typing import Any, cast

from numpy.random import default_rng

from dhash.routing.guard import check_guard_phase
from dhash.routing.router import DHash
from dhash.routing.window import select_window_route
from dhash_repro.benchmark.collectors import load_stddev
from dhash_repro.config.defaults import DATASET_DEFAULTS, NODES, SEED, VIRTUAL_POINTS_PER_NODE
from dhash_repro.dataset.loader import load_dataset_workload_base
from dhash_repro.workloads import zipf as zipf_module
from dhash_repro.workloads.zipf import generate_zipf_workload


@dataclass(frozen=True)
class AlternateSelectionInfo:
    key: str
    primary_point: int
    primary_node: str
    virtual_alt_point: int
    virtual_alt_node: str
    physical_alt_point: int
    physical_alt_node: str


class VirtualAlternateDHash(DHash):  # type: ignore[misc]
    def _ensure_alternate(self, key: Any, primary: str) -> None:
        if key in self.alt:
            return

        info = describe_alternate_candidates(self, str(key))
        self.alt[key] = info.virtual_alt_node

    def get_node(self, key: Any, op: str = "read") -> str:
        self._sync_membership_if_needed()

        if op == "write":
            return cast(str, self._primary_safe(key))

        cnt = self.reads.get(key, 0) + 1
        self.reads[key] = cnt

        if cnt < self.T and key not in self.alt:
            return cast(str, self._primary_safe(key))

        primary = cast(str, self._primary_safe(key))
        self._ensure_alternate(key, primary)

        if check_guard_phase(cnt, self.T, self.W):
            return primary

        return cast(str, select_window_route(cnt, self.T, self.W, primary, self.alt[key]))


class PhysicalAlternateDHash(DHash):  # type: ignore[misc]
    def _ensure_alternate(self, key: Any, primary: str) -> None:
        if key in self.alt:
            return

        info = describe_alternate_candidates(self, str(key))
        self.alt[key] = info.physical_alt_node

    def get_node(self, key: Any, op: str = "read") -> str:
        self._sync_membership_if_needed()

        if op == "write":
            return cast(str, self._primary_safe(key))

        cnt = self.reads.get(key, 0) + 1
        self.reads[key] = cnt

        if cnt < self.T and key not in self.alt:
            return cast(str, self._primary_safe(key))

        primary = cast(str, self._primary_safe(key))
        self._ensure_alternate(key, primary)

        if check_guard_phase(cnt, self.T, self.W):
            return primary

        return cast(str, select_window_route(cnt, self.T, self.W, primary, self.alt[key]))


def describe_alternate_candidates(router: DHash, key: str) -> AlternateSelectionInfo:
    ring_keys = cast(list[int], getattr(router.ch, "sorted_keys", []))
    ring_map = cast(dict[int, str], getattr(router.ch, "ring", {}))
    if not ring_keys or not ring_map:
        raise ValueError("Consistent hashing ring is empty.")

    hk = router._h(key)
    primary_index = bisect(ring_keys, hk) % len(ring_keys)
    primary_point = ring_keys[primary_index]
    primary_node = ring_map[primary_point]

    virtual_point = primary_point
    virtual_node = primary_node
    for offset in range(1, len(ring_keys) + 1):
        candidate_point = ring_keys[(primary_index + offset) % len(ring_keys)]
        if candidate_point == primary_point:
            continue
        virtual_point = candidate_point
        virtual_node = ring_map[candidate_point]
        break

    seen_nodes: set[str] = set()
    physical_point = primary_point
    physical_node = primary_node
    for offset in range(1, len(ring_keys) + 1):
        candidate_point = ring_keys[(primary_index + offset) % len(ring_keys)]
        candidate_node = ring_map[candidate_point]
        if candidate_node == primary_node or candidate_node in seen_nodes:
            continue
        seen_nodes.add(candidate_node)
        physical_point = candidate_point
        physical_node = candidate_node
        break

    return AlternateSelectionInfo(
        key=key,
        primary_point=primary_point,
        primary_node=primary_node,
        virtual_alt_point=virtual_point,
        virtual_alt_node=virtual_node,
        physical_alt_point=physical_point,
        physical_alt_node=physical_node,
    )


class CompareVirtualVsPhysicalAlternate:
    def __init__(
        self,
        datasets: tuple[str, ...] = tuple(DATASET_DEFAULTS.keys()),
        alpha: float = 1.5,
        threshold: int = 300,
        window_size: int = 200,
        seed: int = SEED,
    ) -> None:
        self.datasets = datasets
        self.alpha = alpha
        self.threshold = threshold
        self.window_size = window_size
        self.seed = seed
        self.results: dict[str, dict[str, Any]] = {}

    def _load_ranked_keys_and_workload(self, dataset: str) -> tuple[list[str], list[str]]:
        raw_keys, total_requests = load_dataset_workload_base(dataset)
        ranked_keys = [key for key, _ in Counter(raw_keys).most_common()]
        zipf_module.NP_RNG = default_rng(self.seed)
        workload = generate_zipf_workload(ranked_keys, size=total_requests, alpha=self.alpha)
        return ranked_keys, [str(key) for key in workload]

    def _build_virtual_router(self, nodes: list[str]) -> VirtualAlternateDHash:
        return VirtualAlternateDHash(
            nodes,
            hot_key_threshold=self.threshold,
            window_size=self.window_size,
            replicas=VIRTUAL_POINTS_PER_NODE,
        )

    def _build_physical_router(self, nodes: list[str]) -> PhysicalAlternateDHash:
        return PhysicalAlternateDHash(
            nodes,
            hot_key_threshold=self.threshold,
            window_size=self.window_size,
            replicas=VIRTUAL_POINTS_PER_NODE,
        )

    def _evaluate_alternate_pairs(
        self,
        router: DHash,
        keys: list[str],
        mode: str,
    ) -> tuple[int, list[AlternateSelectionInfo]]:
        same_physical_examples: list[AlternateSelectionInfo] = []
        same_physical_count = 0

        for key in keys:
            info = describe_alternate_candidates(router, key)

            if mode == "virtual":
                is_same = info.virtual_alt_node == info.primary_node
                is_example = (
                    info.virtual_alt_node == info.primary_node
                    and info.physical_alt_node != info.primary_node
                )
            elif mode == "physical":
                is_same = info.physical_alt_node == info.primary_node
                is_example = False
            else:
                raise ValueError(f"Unknown mode: {mode}")

            if is_same:
                same_physical_count += 1
            if is_example and len(same_physical_examples) < 5:
                same_physical_examples.append(info)

        return same_physical_count, same_physical_examples

    def _route_workload(self, router: DHash, workload: list[str]) -> dict[str, int]:
        node_load: Counter[str] = Counter()
        for key in workload:
            node_load[router.get_node(key, op="read")] += 1
        return {node: int(node_load.get(node, 0)) for node in NODES}

    @staticmethod
    def _max_node_share(node_load: dict[str, int]) -> float:
        total = sum(node_load.values())
        return (max(node_load.values()) / total) if total > 0 else 0.0

    def _run_strategy(
        self,
        strategy_name: str,
        router: DHash,
        evaluated_keys: list[str],
        workload: list[str],
        mode: str,
    ) -> dict[str, Any]:
        same_physical_count, examples = self._evaluate_alternate_pairs(router, evaluated_keys, mode)
        routing_router = type(router)(
            NODES,
            hot_key_threshold=self.threshold,
            window_size=self.window_size,
            replicas=VIRTUAL_POINTS_PER_NODE,
        )
        node_load = self._route_workload(routing_router, workload)
        evaluated_key_count = len(evaluated_keys)

        return {
            "strategy_name": strategy_name,
            "evaluated_keys": evaluated_key_count,
            "same_physical_count": same_physical_count,
            "same_physical_ratio": (
                same_physical_count / evaluated_key_count if evaluated_key_count > 0 else 0.0
            ),
            "node_load": node_load,
            "load_stddev": float(load_stddev(node_load)),
            "max_node_share": self._max_node_share(node_load),
            "examples": examples,
        }

    def run(self) -> dict[str, dict[str, Any]]:
        results: dict[str, dict[str, Any]] = {}

        for dataset in self.datasets:
            ranked_keys, workload = self._load_ranked_keys_and_workload(dataset)
            virtual_result = self._run_strategy(
                "가상 노드 기반 alternate",
                self._build_virtual_router(NODES),
                ranked_keys,
                workload,
                mode="virtual",
            )
            physical_result = self._run_strategy(
                "물리 노드 기반 alternate",
                self._build_physical_router(NODES),
                ranked_keys,
                workload,
                mode="physical",
            )
            results[dataset] = {
                "virtual": virtual_result,
                "physical": physical_result,
            }

        self.results = results
        return results

    def print_results(self) -> None:
        results = self.results if self.results else self.run()

        for dataset, dataset_result in results.items():
            virtual = dataset_result["virtual"]
            physical = dataset_result["physical"]

            print()
            print(f"===== 데이터셋: {dataset.upper()} =====")
            print("현재 구현 기준")
            print(
                "  - primary 선택: router.py 의 _primary_safe() 에서 bisect로 첫 가상 포인트 선택"
            )
            print("  - alternate 비교: 가상 노드 기준 vs 물리 노드 dedup 기준")
            print("  - 매핑 방식: ring[virtual_point] -> physical node")
            print()
            print("=== 가상 노드 기반 alternate ===")
            print(f"평가한 key 수: {virtual['evaluated_keys']:,}")
            print(f"same physical 개수: {virtual['same_physical_count']:,}")
            print(f"same physical 비율: {virtual['same_physical_ratio'] * 100:.2f}%")
            print(f"Load Stddev: {virtual['load_stddev']:,.3f}")
            print(f"최대 노드 점유율: {virtual['max_node_share'] * 100:.2f}%")
            print()
            print("=== 물리 노드 기반 alternate ===")
            print(f"평가한 key 수: {physical['evaluated_keys']:,}")
            print(f"same physical 개수: {physical['same_physical_count']:,}")
            print(f"same physical 비율: {physical['same_physical_ratio'] * 100:.2f}%")
            print(f"Load Stddev: {physical['load_stddev']:,.3f}")
            print(f"최대 노드 점유율: {physical['max_node_share'] * 100:.2f}%")
            print()
            same_ratio_before = virtual["same_physical_ratio"] * 100.0
            same_ratio_after = physical["same_physical_ratio"] * 100.0
            load_delta = float(virtual["load_stddev"]) - float(physical["load_stddev"])
            load_improvement = (
                load_delta / float(virtual["load_stddev"]) * 100.0
                if float(virtual["load_stddev"]) > 0
                else 0.0
            )
            print("=== 개선 요약 ===")
            print(f"same physical 비율: {same_ratio_before:.2f}% -> {same_ratio_after:.2f}%")
            print(
                f"Load Stddev: {float(virtual['load_stddev']):,.3f} -> "
                f"{float(physical['load_stddev']):,.3f}  "
                f"(delta {load_delta:,.3f}, 개선 {load_improvement:.2f}%)"
            )
            print(
                f"최대 노드 점유율: {virtual['max_node_share'] * 100:.2f}% -> "
                f"{physical['max_node_share'] * 100:.2f}%"
            )
            print()
            print("=== 대표 예시 key ===")
            examples: list[AlternateSelectionInfo] = virtual["examples"]
            if not examples:
                print("가상 노드 기준에서 same physical 사례를 찾지 못했습니다.")
            else:
                for example in examples:
                    print(f"key: {example.key}")
                    print(
                        f"  primary  : virtual_point={example.primary_point} / "
                        f"physical={example.primary_node}"
                    )
                    print(
                        f"  가상 기반 a(k): virtual_point={example.virtual_alt_point} / "
                        f"physical={example.virtual_alt_node}"
                    )
                    print(
                        f"  물리 기반 a(k): virtual_point={example.physical_alt_point} / "
                        f"physical={example.physical_alt_node}"
                    )


def test_physical_alternate_avoids_same_physical_node() -> None:
    base_keys, _ = load_dataset_workload_base("nasa")
    ranked_keys = [key for key, _ in Counter(base_keys).most_common()]
    sample_keys = ranked_keys[:500]

    experiment = CompareVirtualVsPhysicalAlternate(datasets=("nasa",))
    router = experiment._build_physical_router(NODES)

    same_physical_count, _ = experiment._evaluate_alternate_pairs(
        router,
        sample_keys,
        mode="physical",
    )
    assert same_physical_count == 0


def test_virtual_alternate_produces_same_physical_cases() -> None:
    base_keys, _ = load_dataset_workload_base("nasa")
    ranked_keys = [key for key, _ in Counter(base_keys).most_common()]
    sample_keys = ranked_keys[:500]

    experiment = CompareVirtualVsPhysicalAlternate(datasets=("nasa",))
    router = experiment._build_virtual_router(NODES)

    same_physical_count, _ = experiment._evaluate_alternate_pairs(
        router,
        sample_keys,
        mode="virtual",
    )

    assert same_physical_count > 0


if __name__ == "__main__":
    CompareVirtualVsPhysicalAlternate().print_results()
