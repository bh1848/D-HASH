from typing import Any, List
import numpy as np
from ..config.defaults import NP_RNG


def generate_zipf_workload(keys: List[Any], size: int, alpha: float = 1.1) -> List[Any]:
    if not keys:
        raise ValueError("Key list is empty.")
    n = len(keys)
    ranks = np.arange(1, n + 1, dtype=np.float64)
    weights = ranks ** (-alpha)
    probabilities = weights / weights.sum()
    indices = NP_RNG.choice(n, size=size, replace=True, p=probabilities)
    return [keys[i] for i in indices]
