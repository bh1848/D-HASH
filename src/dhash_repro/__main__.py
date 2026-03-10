import logging
import os

from dhash_repro.experiment import run_experiments

logger = logging.getLogger(__name__)


def _get_mode() -> str:
    return os.getenv("DHASH_MODE", "all").strip().lower()


def _get_alpha() -> float:
    return float(os.getenv("DHASH_ALPHA", "1.5"))


def _get_repeats() -> int:
    return int(os.getenv("DHASH_REPEATS", "1"))


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )

    mode = _get_mode()
    alpha = _get_alpha()
    repeats = _get_repeats()

    logger.info("Starting D-HASH experiments (mode=%s, alpha=%s, repeats=%s)", mode, alpha, repeats)
    run_experiments(mode=mode, alpha=alpha, repeats=repeats)


if __name__ == "__main__":
    main()
