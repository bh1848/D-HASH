"""
Window-based routing logic for D-HASH.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any


def pick_node_by_window(
    *,
    delta: int,
    W: int,
    alt_node: str,
    primary_fn: Callable[[Any], str],
    key: Any,
) -> str:
    """
    Window-based Traffic Switching.

    This matches:
        epoch = (delta - W) // W
        return alt if epoch % 2 == 0 else primary
    """
    epoch = (delta - W) // W
    return alt_node if (epoch % 2 == 0) else primary_fn(key)
