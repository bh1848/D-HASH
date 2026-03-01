"""
Configuration & Global Constants.

This module defines the static hyperparameters for the experiment
(e.g., node count, replication factor, TTL) and manages global state
such as the random number generator (RNG) seed.
"""

from __future__ import annotations

import importlib.util as _importlib_util
import logging
import platform
from typing import Any

import numpy as np
from numpy.random import default_rng

# -----------------------------------------------------------------------------
# Infrastructure Configuration
# -----------------------------------------------------------------------------
NODES: list[str] = [f"redis-{i}" for i in range(1, 6)]  # redis-1 to redis-5
REPLICAS: int = 100
TTL_SECONDS: int = 600
PIPELINE_SIZE_DEFAULT: int = 500
VALUE_BYTES: int = 0  # 0 means minimal payload (key-only focus)

# -----------------------------------------------------------------------------
# Experiment Parameters
# -----------------------------------------------------------------------------
NUM_REPEATS: int = 10  # Repetitions for statistical significance

# Zipfian Workload Settings
ZIPF_ALPHAS: list[float] = [1.1, 1.3, 1.5]
PIPELINE_SWEEP: list[int] = [50, 100, 200, 500, 1000]
ABLAT_THRESHOLDS: list[int] = [100, 200, 300, 500, 800]

# Microbenchmark Settings
SEED: int = 1337
MICROBENCH_OPS: int = 2_000_000
MICROBENCH_NUM_KEYS: int = 10_000

# -----------------------------------------------------------------------------
# Global State (RNG)
# -----------------------------------------------------------------------------
# Shared Numpy RNG instance for consistent workload generation across modules
NP_RNG = default_rng(SEED)


def reset_np_rng(seed: int) -> None:
    """Resets the global random number generator with a new seed."""
    global NP_RNG
    NP_RNG = default_rng(seed)


# -----------------------------------------------------------------------------
# Logging Setup
# -----------------------------------------------------------------------------
def setup_logging(level: int = logging.INFO) -> None:
    """Configures the root logger. Should be called once from the entry point."""
    logging.basicConfig(
        level=level, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S"
    )


logger = logging.getLogger(__name__)


# -----------------------------------------------------------------------------
# Metadata Helper
# -----------------------------------------------------------------------------
def runtime_env_metadata(repeats: int = NUM_REPEATS) -> dict[str, Any]:
    """Returns a dictionary of environment versions for reproducibility reports."""
    import redis as _redis_pkg

    hiredis_enabled = _importlib_util.find_spec("hiredis") is not None

    return {
        "seed": SEED,
        "python": platform.python_version(),
        "numpy": np.__version__,
        "redis_py": _redis_pkg.__version__,
        "hiredis": hiredis_enabled,
        "nodes": ",".join(NODES),
        "replicas": REPLICAS,
        "repeats": repeats,
    }
