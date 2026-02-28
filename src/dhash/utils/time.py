"""
Time utilities.

Extracted from benchmark-related timing code.
No logic change.
"""

from __future__ import annotations

import time


def now_ns() -> int:
    return time.perf_counter_ns()


def now() -> float:
    return time.perf_counter()
