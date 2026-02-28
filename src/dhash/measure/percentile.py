"""
Weighted percentile calculation.

Moved from dhash_experiments.bench._weighted_percentile without logic changes.
"""

from __future__ import annotations


def _weighted_percentile(samples: list[tuple[float, int]], q: float) -> float:
    """
    Calculates a weighted percentile from aggregated samples.

    Since we use pipelining, a single latency sample represents 'N' operations.
    This function expands those weights to calculate accurate P95/P99 latency.

    Args:
        samples: List of (avg_latency_per_op, batch_size)
        q: Quantile (e.g., 0.99 for 99th percentile)
    """
    if not samples:
        return 0.0

    # Sort by latency
    samples_sorted = sorted(samples, key=lambda x: x[0])
    total_w = sum(w for _, w in samples_sorted)

    if total_w <= 0:
        return 0.0

    target = q * total_w
    cum = 0.0
    prev_v = samples_sorted[0][0]

    for v, w in samples_sorted:
        next_cum = cum + w
        if next_cum >= target:
            if w == 0:
                return v
            # Linear interpolation
            frac = (target - cum) / w
            return prev_v + (v - prev_v) * frac
        prev_v = v
        cum = next_cum

    return samples_sorted[-1][0]


# Public-friendly alias (same implementation)
def weighted_percentile(samples: list[tuple[float, int]], q: float) -> float:
    return _weighted_percentile(samples, q)
