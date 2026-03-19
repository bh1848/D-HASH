import logging
import os
from typing import List, Optional

from dhash_repro.config.defaults import NUM_REPEATS
from dhash_repro.experiment import run_experiments

logger = logging.getLogger(__name__)


def _get_mode() -> str:
    return os.getenv("DHASH_MODE", "all").strip().lower()


def _get_alpha() -> float:
    return float(os.getenv("DHASH_ALPHA", "1.5"))


def _get_dataset_filter() -> str:
    dataset_filter = os.getenv("DHASH_DATASET_FILTER", "").strip()
    if dataset_filter:
        return dataset_filter
    legacy_dataset = os.getenv("DHASH_DATASET", "").strip()
    return legacy_dataset or "ALL"


def _get_optional_int(env_name: str) -> Optional[int]:
    raw = os.getenv(env_name, "").strip()
    return int(raw) if raw else None


def _get_algos() -> str:
    return os.getenv("DHASH_ALGOS", "auto").strip().lower()


def _get_algos_list() -> str:
    return os.getenv("DHASH_ALGOS_LIST", "").strip()


def _get_repeats() -> int:
    return int(os.getenv("DHASH_REPEATS", str(NUM_REPEATS)))


def _get_zipf_alphas() -> Optional[List[float]]:
    raw = os.getenv("DHASH_ZIPF_ALPHAS", "").strip()
    if not raw:
        return None
    return [float(part.strip()) for part in raw.split(",") if part.strip()]


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )

    mode = _get_mode()
    alpha = _get_alpha()
    repeats = _get_repeats()
    dataset_filter = _get_dataset_filter()
    fixed_window = _get_optional_int("DHASH_FIXED_WINDOW")
    dhash_t = _get_optional_int("DHASH_DHASH_T")
    pipeline_for_zipf = _get_optional_int("DHASH_PIPELINE_FOR_ZIPF")
    algos = _get_algos()
    algos_list = _get_algos_list()
    zipf_alphas = _get_zipf_alphas()

    logger.info(
        "Starting D-HASH experiments (mode=%s, alpha=%s, repeats=%s, dataset_filter=%s, algos=%s, zipf_alphas=%s)",
        mode,
        alpha,
        repeats,
        dataset_filter,
        algos,
        zipf_alphas,
    )
    run_experiments(
        mode=mode,
        alpha=alpha,
        repeats=repeats,
        dataset_filter=dataset_filter,
        fixed_window=fixed_window,
        dhash_t=dhash_t,
        pipeline_for_zipf=pipeline_for_zipf,
        algos=algos,
        algos_list=algos_list,
        zipf_alphas=zipf_alphas,
    )


if __name__ == "__main__":
    main()
