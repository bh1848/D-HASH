from collections import Counter
from typing import Any, Dict, List

import pytest

from dhash.hashing.core import ConsistentHashing
from dhash.routing.router import DHash


def _routing_ratio(
    router: DHash,
    key: str,
    n_reads: int,
) -> Dict[str, float]:
    counter: Counter[str] = Counter()
    for _ in range(n_reads):
        node = router.get_node(key, op="read")
        counter[node] += 1
    total = sum(counter.values())
    return {node: count / total for node, count in counter.items()}


def _measure_refreshed_alt(
    key: str,
    nodes_before: List[str],
    nodes_after: List[str],
    threshold: int,
    window_size: int,
    n_reads: int,
) -> Dict[str, Any]:
    router = DHash(nodes_before, hot_key_threshold=threshold, window_size=window_size)

    for _ in range(threshold + window_size + 1):
        router.get_node(key, op="read")

    primary_before = router._primary_safe(key)
    alt_before = router.alt[key]

    router.refresh_membership(nodes_after)
    primary_after = router._primary_safe(key)

    router.reads[key] = threshold + window_size + 1
    ratio_after = _routing_ratio(router, key, n_reads)
    alt_after = router.alt.get(key)

    return {
        "primary_before": primary_before,
        "alt_before": alt_before,
        "primary_after": primary_after,
        "alt_after": alt_after,
        "ratio_after": ratio_after,
    }


def test_stale_alt_causes_wrong_routing_ratio() -> None:
    nodes_before = ["redis-1", "redis-2", "redis-3", "redis-4", "redis-5"]
    T = 10
    W = 10
    N_READS = 1000
    key = "key-13"

    router = DHash(nodes_before, hot_key_threshold=T, window_size=W)

    for _ in range(T + W + 1):
        router.get_node(key, op="read")

    primary_before = router._primary_safe(key)
    alt_before = router.alt[key]

    assert primary_before != alt_before, "primary와 alt는 달라야 한다"

    ratio_before = _routing_ratio(router, key, N_READS)
    print(f"\n[변경 전] primary={primary_before}, alt={alt_before}")
    print(f"  라우팅 비율: {ratio_before}")

    p_ratio = ratio_before.get(primary_before, 0)
    a_ratio = ratio_before.get(alt_before, 0)
    assert abs(p_ratio - 0.5) < 0.1, f"변경 전 primary 비율이 0.5에서 벗어남: {p_ratio:.3f}"
    assert abs(a_ratio - 0.5) < 0.1, f"변경 전 alt 비율이 0.5에서 벗어남: {a_ratio:.3f}"

    nodes_after = nodes_before + ["redis-6"]
    new_ring = ConsistentHashing(nodes_after, replicas=100)

    router.ch = new_ring
    router.nodes = nodes_after
    router._ring_signature = router._compute_ring_signature()

    primary_after = router._primary_safe(key)
    alt_stale = router.alt[key]

    print(f"\n[변경 후 stale] primary={primary_after}, alt(stale)={alt_stale}")

    if primary_after != primary_before:
        print(f"  → primary 변경됨: {primary_before} → {primary_after}")
        print(f"  → alt는 stale: {alt_stale} (새 primary 기준으로 재계산되지 않음)")

        router.reads[key] = T + W + 1
        ratio_stale = _routing_ratio(router, key, N_READS)
        print(f"  라우팅 비율(stale): {ratio_stale}")

        assert alt_stale in ratio_stale, f"stale alt({alt_stale})로 요청이 가야 한다"
        stale_a_ratio = ratio_stale.get(alt_stale, 0)
        print(f"  stale alt({alt_stale}) 비율: {stale_a_ratio:.3f}")
        print(f"  새 primary({primary_after}) read 비율: {ratio_stale.get(primary_after, 0):.3f}")
    else:
        print("  → primary 변경 없음 (이 키는 영향받지 않음), alt stale 테스트 스킵")
        pytest.skip("이 키의 primary는 멤버십 변경에 영향받지 않음")


def test_alt_clear_restores_correct_routing_ratio() -> None:
    nodes_before = ["redis-1", "redis-2", "redis-3", "redis-4", "redis-5"]
    T = 10
    W = 10
    N_READS = 2000
    key = "key-13"

    router = DHash(nodes_before, hot_key_threshold=T, window_size=W)

    for _ in range(T + W + 1):
        router.get_node(key, op="read")

    primary_before = router._primary_safe(key)
    alt_before = router.alt[key]
    print(f"\n[변경 전] primary={primary_before}, alt={alt_before}")

    nodes_after = nodes_before + ["redis-6"]
    router.refresh_membership(nodes_after)

    primary_after = router._primary_safe(key)
    print(f"[변경 후] primary={primary_after}")
    print("  alt 캐시 비움 → 다음 read에서 재계산")

    router.reads[key] = T + W + 1
    ratio_after = _routing_ratio(router, key, N_READS)

    alt_after = router.alt.get(key)
    print(f"  새 alt={alt_after}")
    print(f"  라우팅 비율: {ratio_after}")

    assert alt_after is not None
    assert alt_after != primary_after, "새 alt는 새 primary와 달라야 한다"
    assert set(ratio_after.keys()) == {primary_after, alt_after}, (
        f"라우팅이 의도된 두 노드({primary_after}, {alt_after})에서만 일어나야 한다. "
        f"실제: {set(ratio_after.keys())}"
    )

    p_ratio = ratio_after.get(primary_after, 0)
    a_ratio = ratio_after.get(alt_after, 0)
    print(f"  primary 비율: {p_ratio:.3f}, alt 비율: {a_ratio:.3f}")
    assert abs(p_ratio - 0.5) < 0.1, f"primary 비율이 0.5에서 벗어남: {p_ratio:.3f}"
    assert abs(a_ratio - 0.5) < 0.1, f"alt 비율이 0.5에서 벗어남: {a_ratio:.3f}"


def test_routing_ratio_summary() -> None:
    nodes_before = ["redis-1", "redis-2", "redis-3", "redis-4", "redis-5"]
    nodes_after = nodes_before + ["redis-6"]
    T = 10
    W = 10
    N_READS = 2000

    keys = [f"key-{i}" for i in range(50)]

    primary_changed = 0
    stale_causes_wrong_node = 0
    total_keys = len(keys)
    refreshed_records: List[Dict[str, Any]] = []

    print("\n=== 멤버십 변경 시 라우팅 비율 요약 ===")

    for key in keys:
        router = DHash(nodes_before, hot_key_threshold=T, window_size=W)
        for _ in range(T + W + 1):
            router.get_node(key, op="read")

        primary_before = router._primary_safe(key)
        alt_before = router.alt[key]

        new_ring = ConsistentHashing(nodes_after, replicas=100)
        router.ch = new_ring
        router.nodes = nodes_after
        router._ring_signature = router._compute_ring_signature()
        primary_after = router._primary_safe(key)

        if primary_after != primary_before:
            primary_changed += 1
            refreshed = _measure_refreshed_alt(
                key=key,
                nodes_before=nodes_before,
                nodes_after=nodes_after,
                threshold=T,
                window_size=W,
                n_reads=N_READS,
            )
            refreshed_records.append({"key": key, **refreshed})
            print(
                "  primary 변경: "
                f"key={key}, "
                f"{primary_before} → {primary_after}, "
                f"stale alt={alt_before}, "
                f"정상 alt={refreshed['alt_after']}"
            )

            if alt_before != primary_after:
                stale_causes_wrong_node += 1

    if refreshed_records:
        print("\n  [정상 a(k) 상세]")
        for record in refreshed_records:
            ratio_after = record["ratio_after"]
            primary_after = record["primary_after"]
            alt_after = record["alt_after"]
            print(
                "  "
                f"{record['key']}: "
                f"새 p(k)={primary_after}, "
                f"stale a(k)={record['alt_before']}, "
                f"정상 a(k)={alt_after}, "
                f"정상 비율={ratio_after}"
            )
            assert alt_after is not None
            assert alt_after != primary_after
            assert set(ratio_after.keys()) == {primary_after, alt_after}

    print(f"전체 키: {total_keys}개")
    print(f"primary 변경된 키: {primary_changed}개 ({primary_changed / total_keys * 100:.1f}%)")
    print(f"  → stale alt가 새 p(k)와 다른 노드 쌍을 만드는 키: {stale_causes_wrong_node}개")
    print(f"  → 이론값 1/(|N|+1) = 1/6 ≈ {1 / 6 * 100:.1f}%")

    assert (
        abs(primary_changed / total_keys - 1 / 6) < 0.15
    ), f"primary 변경 비율이 이론값과 너무 다름: {primary_changed / total_keys:.3f}"
