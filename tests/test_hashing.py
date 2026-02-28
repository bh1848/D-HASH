from __future__ import annotations

from dhash.hashing import (
    ConsistentHashing,
    RendezvousHashing,
    WeightedConsistentHashing,
    fast_hash64,
)


def test_fast_hash64_deterministic() -> None:
    a = fast_hash64("hello")
    b = fast_hash64("hello")
    c = fast_hash64("world")

    assert isinstance(a, int)
    assert a == b
    assert a != c


def test_consistent_hashing_deterministic() -> None:
    nodes = ["n1", "n2", "n3"]
    ch = ConsistentHashing(nodes, replicas=50)

    k = "k123"
    n1 = ch.get_node(k)
    n2 = ch.get_node(k)

    assert n1 in nodes
    assert n1 == n2


def test_weighted_consistent_hashing_runs() -> None:
    nodes = ["n1", "n2", "n3"]
    w = {"n1": 2.0, "n2": 1.0, "n3": 1.0}
    ch = WeightedConsistentHashing(nodes, weights=w, base_replicas=50)

    n = ch.get_node("k123")
    assert n in nodes


def test_rendezvous_hashing_runs() -> None:
    nodes = ["n1", "n2", "n3"]
    rh = RendezvousHashing(nodes)

    n = rh.get_node("k123")
    assert n in nodes
