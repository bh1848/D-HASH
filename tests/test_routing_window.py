from __future__ import annotations

from dhash.routing import DHash


def test_window_routing_toggles_after_guard() -> None:
    nodes = ["n1", "n2", "n3"]
    T = 1
    W = 3
    r = DHash(nodes=nodes, hot_key_threshold=T, window_size=W, replicas=50)

    key = "k"

    # 1st read: cnt=1 cold
    primary = r.get_node(key, op="read")

    # 2nd read: cnt=2 promote, delta=1 -> guard
    assert r.get_node(key, op="read") == primary
    assert key in r.alt
    alt = r.alt[key]
    assert alt != primary

    # advance until guard ends: need delta reach W
    # currently cnt=2 => delta=1. We need delta=3 => cnt = T + delta = 1 + 3 = 4
    # so do reads until cnt=4 (two more reads).
    assert r.get_node(key, op="read") == primary  # cnt=3, delta=2 (guard)
    # cnt=4, delta=3 => guard 끝, epoch=(3-3)//3=0 => alt
    assert r.get_node(key, op="read") == alt

    # next window: delta=4..5 still epoch=0 => alt
    assert r.get_node(key, op="read") == alt  # cnt=5, delta=4
    assert r.get_node(key, op="read") == alt  # cnt=6, delta=5

    # delta=6 => epoch=(6-3)//3=1 => primary
    assert r.get_node(key, op="read") == primary  # cnt=7, delta=6
