from __future__ import annotations

from dhash.routing import DHash


def test_write_always_routes_to_primary() -> None:
    nodes = ["n1", "n2", "n3"]
    r = DHash(nodes=nodes, hot_key_threshold=1, window_size=3, replicas=50)

    key = "k"
    p = r.get_node(key, op="write")
    for _ in range(10):
        assert r.get_node(key, op="write") == p


def test_guard_phase_sticks_to_primary_after_promotion() -> None:
    nodes = ["n1", "n2", "n3"]
    T = 2
    W = 4
    r = DHash(nodes=nodes, hot_key_threshold=T, window_size=W, replicas=50)

    key = "hot"

    # warm up reads to reach promotion boundary
    p = r.get_node(key, op="read")  # cnt=1
    assert (
        r.get_node(key, op="read") == p
    )  # cnt=2 (still cold in our condition cnt < T and not alt)

    # next read: cnt=3 => promote (alt assigned), delta=1
    assert r.get_node(key, op="read") == p  # guard (delta=1 < W)

    # keep within guard: delta=2..W-1
    for _ in range(W - 2):  # already at delta=1, do W-2 more => last delta=W-1
        assert r.get_node(key, op="read") == p
