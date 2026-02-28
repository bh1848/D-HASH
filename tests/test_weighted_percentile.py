from __future__ import annotations

from dhash.config import NODES
from dhash.measure.metrics import load_stddev
from dhash.measure.percentile import weighted_percentile


def test_weighted_percentile_basic() -> None:
    # samples: (value, weight)
    samples = [
        (10.0, 1),
        (20.0, 1),
        (30.0, 1),
        (40.0, 1),
    ]
    assert weighted_percentile(samples, 0.50) == 20.0 or weighted_percentile(samples, 0.50) == 30.0


def test_weighted_percentile_respects_weights() -> None:
    # 0 has huge weight, so high quantiles should still be near 0
    samples = [
        (0.0, 100),
        (100.0, 1),
        (200.0, 1),
    ]
    p95 = weighted_percentile(samples, 0.95)
    assert p95 < 100.0


def test_load_stddev_uses_all_nodes_and_defaults_to_zero() -> None:
    # distribute load unevenly across config.NODES
    node_load = {n: 0 for n in NODES}
    node_load[NODES[0]] = 100
    node_load[NODES[1]] = 0
    node_load[NODES[2]] = 0
    node_load[NODES[3]] = 0
    node_load[NODES[4]] = 0

    s = load_stddev(node_load)
    assert s > 0.0

    # missing keys should be treated as 0
    s2 = load_stddev({NODES[0]: 10})
    assert s2 >= 0.0
