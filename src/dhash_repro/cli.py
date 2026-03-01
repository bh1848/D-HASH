import argparse
import sys
from .config.defaults import setup_logging
from .experiment import run_experiments


def main() -> None:
    setup_logging()
    parser = argparse.ArgumentParser(description="D-HASH Experiment Runner")
    parser.add_argument(
        "--mode", type=str, choices=["all", "pipeline", "zipf", "ablation"], default="all"
    )
    parser.add_argument("--alpha", type=float, default=1.5)
    parser.add_argument("--repeats", type=int, default=10)

    args = parser.parse_args()
    print(f"[*] Starting D-HASH Experiments (Mode: {args.mode})")

    try:
        run_experiments(mode=args.mode, alpha=args.alpha, repeats=args.repeats)
    except KeyboardInterrupt:
        print("\n[!] Interrupted by user.")
        sys.exit(130)


if __name__ == "__main__":
    main()
