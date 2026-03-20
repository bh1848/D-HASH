from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

import pytest

from dhash.hashing.core import ConsistentHashing
from dhash.routing.router import DHash


@dataclass(frozen=True)
class MembershipChangeSummary:
    key: str
    primary_before: str
    primary_after: str
    stale_alt: str
    refreshed_alt: str


def _push_to_hot_state(router: DHash, key: str, threshold: int, window_size: int) -> None:
    for _ in range(threshold + window_size + 1):
        router.get_node(key, op="read")
    router.reads[key] = threshold + window_size + 1


def _build_before_router(
    nodes_before: list[str],
    key: str,
    threshold: int,
    window_size: int,
) -> tuple[DHash, str, str]:
    router = DHash(nodes_before, hot_key_threshold=threshold, window_size=window_size)
    _push_to_hot_state(router, key, threshold, window_size)
    primary_before = router._primary_safe(key)
    alt_before = router.alt[key]
    router.reads[key] = threshold + window_size + 1
    return router, primary_before, alt_before


def _make_stale_router(
    nodes_before: list[str],
    nodes_after: list[str],
    key: str,
    threshold: int,
    window_size: int,
) -> tuple[DHash, str, str, str]:
    router, primary_before, stale_alt = _build_before_router(
        nodes_before,
        key,
        threshold,
        window_size,
    )
    router.ch = ConsistentHashing(nodes_after, replicas=100)
    router.nodes = nodes_after
    router._ring_signature = router._compute_ring_signature()
    primary_after = router._primary_safe(key)
    router.reads[key] = threshold + window_size + 1
    return router, primary_before, primary_after, stale_alt


def _make_refreshed_router(
    nodes_before: list[str],
    nodes_after: list[str],
    key: str,
    threshold: int,
    window_size: int,
) -> tuple[DHash, str, str]:
    router = DHash(nodes_before, hot_key_threshold=threshold, window_size=window_size)
    _push_to_hot_state(router, key, threshold, window_size)
    router.refresh_membership(nodes_after)
    primary_after = router._primary_safe(key)
    router.reads[key] = threshold + window_size + 1
    router.get_node(key, op="read")
    refreshed_alt = router.alt[key]
    router.reads[key] = threshold + window_size + 1
    return router, primary_after, refreshed_alt


def _node_request_counts(router: DHash, key: str, n_reads: int) -> Counter[str]:
    counts: Counter[str] = Counter()
    for _ in range(n_reads):
        counts[router.get_node(key, op="read")] += 1
    return counts


def _routing_ratio(counts: Counter[str]) -> dict[str, float]:
    total = sum(counts.values())
    return {node: count / total for node, count in counts.items()} if total else {}


def _select_representative_key(
    summaries: list[MembershipChangeSummary],
) -> MembershipChangeSummary | None:
    for summary in summaries:
        if summary.stale_alt != summary.refreshed_alt:
            return summary
    return summaries[0] if summaries else None


def _counts_row(label: str, counts: Counter[str], nodes: list[str]) -> str:
    values = "".join(f"{counts.get(node, 0):>9}" for node in nodes)
    return f"{label:<12}{values}"


def test_membership_change_stale_vs_refreshed_summary() -> None:
    nodes_before = ["redis-1", "redis-2", "redis-3", "redis-4", "redis-5"]
    nodes_after = nodes_before + ["redis-6"]
    threshold = 10
    window_size = 10
    representative_reads = 2000
    keys = [f"key-{i}" for i in range(50)]

    changed_summaries: list[MembershipChangeSummary] = []

    for key in keys:
        stale_router, primary_before, primary_after, stale_alt = _make_stale_router(
            nodes_before,
            nodes_after,
            key,
            threshold,
            window_size,
        )
        if primary_after == primary_before:
            continue

        refreshed_router, refreshed_primary, refreshed_alt = _make_refreshed_router(
            nodes_before,
            nodes_after,
            key,
            threshold,
            window_size,
        )

        assert refreshed_primary == primary_after
        assert refreshed_alt != refreshed_primary

        changed_summaries.append(
            MembershipChangeSummary(
                key=key,
                primary_before=primary_before,
                primary_after=primary_after,
                stale_alt=stale_alt,
                refreshed_alt=refreshed_alt,
            )
        )

    if not changed_summaries:
        pytest.fail("membership change 이후 primary가 바뀌는 key를 찾지 못했습니다.")

    primary_changed = len(changed_summaries)
    stale_diff_count = sum(
        1 for summary in changed_summaries if summary.stale_alt != summary.refreshed_alt
    )
    total_keys = len(keys)
    representative = _select_representative_key(changed_summaries)

    assert representative is not None

    before_router, before_primary, before_alt = _build_before_router(
        nodes_before,
        representative.key,
        threshold,
        window_size,
    )
    before_counts = _node_request_counts(before_router, representative.key, representative_reads)
    before_ratio = _routing_ratio(before_counts)

    stale_router, _, stale_primary, stale_alt = _make_stale_router(
        nodes_before,
        nodes_after,
        representative.key,
        threshold,
        window_size,
    )
    stale_counts = _node_request_counts(stale_router, representative.key, representative_reads)
    stale_ratio = _routing_ratio(stale_counts)

    refreshed_router, refreshed_primary, refreshed_alt = _make_refreshed_router(
        nodes_before,
        nodes_after,
        representative.key,
        threshold,
        window_size,
    )
    refreshed_counts = _node_request_counts(
        refreshed_router,
        representative.key,
        representative_reads,
    )
    refreshed_ratio = _routing_ratio(refreshed_counts)

    assert refreshed_alt != refreshed_primary
    assert set(refreshed_counts) == {refreshed_primary, refreshed_alt}
    assert abs(refreshed_ratio.get(refreshed_primary, 0.0) - 0.5) < 0.1
    assert abs(refreshed_ratio.get(refreshed_alt, 0.0) - 0.5) < 0.1

    if stale_alt != refreshed_alt:
        assert stale_alt in stale_counts
        assert set(stale_counts) == {stale_primary, stale_alt}

    print("\n=== Membership Change Representative Summary ===")
    print(f"전체 key 수: {total_keys}")
    print(
        f"primary 변경 key 수: {primary_changed}/{total_keys} "
        f"({primary_changed / total_keys * 100:.1f}%)"
    )
    print(
        f"stale alt != refreshed alt key 수: {stale_diff_count}/{primary_changed} "
        f"({stale_diff_count / primary_changed * 100:.1f}%)"
    )
    print(f"stale alt 발생률: {stale_diff_count}/{primary_changed} -> 0/{primary_changed}")
    print()
    print(
        f"대표 key: {representative.key} "
        f"(before p={before_primary}, stale alt={stale_alt}, refreshed alt={refreshed_alt})"
    )
    print("대표 key 라우팅 비율:")
    print(f"  before    : {before_ratio}")
    print(f"  stale     : {stale_ratio}")
    print(f"  refreshed : {refreshed_ratio}")
    print()
    print("Node Load Distribution:")
    print(f"{'':<12}{''.join(f'{node:>9}' for node in nodes_after)}")
    print(_counts_row("Before", before_counts, nodes_after))
    print(_counts_row("Stale", stale_counts, nodes_after))
    print(_counts_row("Refreshed", refreshed_counts, nodes_after))
