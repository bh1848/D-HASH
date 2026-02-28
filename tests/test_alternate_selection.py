from __future__ import annotations

from dhash.routing import DHash


def test_alternate_differs_from_primary_when_possible() -> None:
    nodes = ["n1", "n2", "n3"]
    # threshold=1로 두 번 읽으면 hot으로 취급되게 만듦
    r = DHash(nodes=nodes, hot_key_threshold=1, window_size=3, replicas=50)

    key = "hotkey"

    # 1st read: cold path (no alt)
    p = r.get_node(key, op="read")
    assert p in nodes

    # 2nd read: promote -> alt allocated
    _ = r.get_node(key, op="read")
    assert key in r.alt

    a = r.alt[key]
    assert a in nodes
    # nodes>=2면 primary와 다른 노드가 선택되는 게 목표
    assert a != p


def test_alternate_may_equal_primary_if_single_node() -> None:
    nodes = ["only"]
    r = DHash(nodes=nodes, hot_key_threshold=1, window_size=3, replicas=10)

    key = "k"
    p = r.get_node(key, op="read")
    _ = r.get_node(key, op="read")  # promote

    assert key in r.alt
    assert r.alt[key] == p
