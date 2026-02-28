"""
Random seed utilities.

Pure helper functions. No routing logic.
"""

from __future__ import annotations

import random

import numpy as np


def seed_everything(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
