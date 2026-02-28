from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class ZipfSpec:
    alpha: float
    num_keys: int


def make_zipf_pmf(alpha: float, num_keys: int) -> np.ndarray:
    """
    Build Zipf PMF over ranks 1..num_keys.
    p(i) ~ 1 / i^alpha
    """
    ranks = np.arange(1, num_keys + 1, dtype=np.float64)
    weights = 1.0 / np.power(ranks, float(alpha))
    pmf = weights / weights.sum()
    return pmf


def sample_zipf_keys(
    *,
    rng: np.random.Generator,
    alpha: float,
    num_keys: int,
    num_ops: int,
    key_prefix: str = "k",
) -> list[str]:
    """
    Samples `num_ops` keys from Zipf(alpha) over `num_keys` distinct keys.
    Returns materialized list for reproducibility and for easier batching.
    """
    pmf = make_zipf_pmf(alpha, num_keys)
    # keys are 0..num_keys-1 (map to prefix)
    idx = rng.choice(num_keys, size=num_ops, replace=True, p=pmf)
    return [f"{key_prefix}{i}" for i in idx.tolist()]


def topk_expected_mass(alpha: float, num_keys: int, k: int) -> float:
    """
    Expected probability mass of top-k hottest keys.
    Helpful for sanity checks / logging.
    """
    pmf = make_zipf_pmf(alpha, num_keys)
    k = max(0, min(int(k), num_keys))
    return float(pmf[:k].sum())
