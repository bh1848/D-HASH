"""
Metrics helpers.

Moved from dhash_experiments.bench.load_stddev without logic changes.
"""

from __future__ import annotations

from statistics import stdev

from ..config import NODES


def load_stddev(node_load: dict[str, int]) -> float:
    """Calculates standard deviation of request counts across nodes."""
    vals = [node_load.get(n, 0) for n in NODES]
    return stdev(vals) if len(vals) > 1 else 0.0
