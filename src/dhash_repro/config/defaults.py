import importlib.util
import logging
import platform
from typing import Any, Dict, List

import numpy as np
from numpy.random import default_rng

from dhash.config import D_HASH_REPLICATION_FACTOR, VIRTUAL_POINTS_PER_NODE

NODES: List[str] = [f"redis-{i}" for i in range(1, 6)]
REDIS_PORT: int = 6379
TTL_SECONDS: int = 600
# Paper-aligned global defaults used when a dataset-specific override is not provided.
PIPELINE_SIZE_DEFAULT: int = 200
THRESHOLD_DEFAULT: int = 300
VALUE_BYTES: int = 0
NUM_REPEATS: int = 10
ZIPF_ALPHAS: List[float] = [1.1, 1.3, 1.5]
PIPELINE_SWEEP: List[int] = [50, 100, 200, 500, 1000]
ABLAT_THRESHOLDS: List[int] = [100, 200, 300, 500, 800]

DEFAULT_DATASET: str = "nasa"
# Paper-selected operating points from Section 4.4 / 4.5.
DATASET_DEFAULTS: Dict[str, Dict[str, float]] = {
    "nasa": {"B": 200, "W": 200, "T": 300, "rho": 1.0},
    "ebay": {"B": 1000, "W": 1000, "T": 300, "rho": 1.0},
}

SEED: int = 1337
MICROBENCH_OPS: int = 2_000_000
MICROBENCH_NUM_KEYS: int = 10_000

NP_RNG = default_rng(SEED)


def reset_np_rng(seed: int) -> None:
    global NP_RNG
    NP_RNG = default_rng(seed)


def setup_logging(level: int = logging.INFO) -> None:
    logging.basicConfig(
        level=level, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S"
    )


logger = logging.getLogger(__name__)


def runtime_env_metadata(repeats: int = NUM_REPEATS) -> Dict[str, Any]:
    import redis as _redis_pkg

    hiredis_spec = importlib.util.find_spec("hiredis")
    hiredis_enabled = hiredis_spec is not None

    return {
        "seed": SEED,
        "python": platform.python_version(),
        "numpy": np.__version__,
        "redis_py": _redis_pkg.__version__,
        "hiredis": hiredis_enabled,
        "nodes": ",".join(NODES),
        "virtual_points_per_node": VIRTUAL_POINTS_PER_NODE,
        "dhash_replication_factor": D_HASH_REPLICATION_FACTOR,
        "ttl": TTL_SECONDS,
        "pipeline": PIPELINE_SIZE_DEFAULT,
        "value_bytes": VALUE_BYTES,
        "repeats": repeats,
    }
