"""
Workload Generation Utilities.

This module is responsible for generating synthetic traffic patterns used in experiments.
It specifically implements the Zipfian (Power-law) distribution generator, 
which mimics real-world access patterns where a few keys (hot-keys) account for 
the majority of the traffic.

Note:
    Legacy data loaders (NASA/eBay) have been removed to ensure 
    standalone reproducibility without external dataset dependencies.
"""
from __future__ import annotations

from typing import Any, List

import numpy as np

from .config import NP_RNG


def generate_zipf_workload(keys: List[Any], size: int, alpha: float = 1.1) -> List[Any]:
    """
    Generates a sequence of key accesses following a Zipfian distribution.

    Args:
        keys: The universe of available keys. The first key in the list will be 
              assigned Rank 1 (most frequent), the second Rank 2, etc.
        size: Total number of access requests to generate (length of the output list).
        alpha: The skewness parameter (alpha > 1). Higher alpha means more skew 
               (more traffic concentrated on fewer keys).

    Returns:
        A list of keys representing the request stream.
    """
    if not keys:
        raise ValueError("Key list is empty.")

    n = len(keys)

    # 1. Calculate Zipfian probabilities for each rank
    # Rank 1 has weight 1^(-alpha), Rank 2 has 2^(-alpha), ...
    ranks = np.arange(1, n + 1, dtype=np.float64)
    weights = ranks ** (-alpha)

    # 2. Normalize to create a probability distribution (sum = 1)
    probabilities = weights / weights.sum()

    # 3. Sample indices based on the calculated probabilities
    # Using the global pre-seeded RNG from config for reproducibility
    indices = NP_RNG.choice(n, size=size, replace=True, p=probabilities)

    # 4. Map indices back to actual key objects
    return [keys[i] for i in indices]
