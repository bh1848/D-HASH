"""
Alternate node selection for D-HASH.
"""

from __future__ import annotations

from bisect import bisect
from typing import Any


def ensure_alternate(self: Any, key: Any) -> None:
    """
    Selects an Alternate Node (A_k) for a hot-key.
    Ensures A_k is distinct from P_k using auxiliary hashing.

    This function is a direct move of the original DHash._ensure_alternate logic.
    """
    if key in self.alt:
        return

    rk = getattr(self.ch, "sorted_keys", None)
    ring = getattr(self.ch, "ring", None)

    if not rk or not ring or len(self.nodes) <= 1:
        # Fallback if cluster is too small
        self.alt[key] = self._primary_safe(key)
        return

    hk = self._h(key)
    i = bisect(rk, hk) % len(rk)
    primary = ring[rk[i]]

    # Use auxiliary hash to find a different node in the ring
    stride_span = max(1, len(self.nodes) - 1)
    stride = 1 + (self._h(f"{key}|alt") % stride_span)

    # 1. Try stride-based selection
    j = i
    for _ in range(len(rk)):
        j = (j + stride) % len(rk)
        cand = ring[rk[j]]
        if cand != primary:
            self.alt[key] = cand
            return

    # 2. Linear scan fallback (rarely hit)
    j = i
    for _ in range(len(rk)):
        j = (j + 1) % len(rk)
        cand = ring[rk[j]]
        if cand != primary:
            self.alt[key] = cand
            return

    self.alt[key] = primary
