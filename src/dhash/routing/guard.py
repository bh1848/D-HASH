"""
Guard phase logic for D-HASH.
"""

from __future__ import annotations


def in_guard_phase(delta: int, W: int) -> bool:
    """
    Guard Phase: Stick to Primary for first W requests after promotion.

    This matches:
        if delta < self.W: return primary
    """
    return delta < W
