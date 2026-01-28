"""
Command Line Interface (CLI) for D-HASH Experiments.

This module serves as the entry point for running various experimental stages.
It parses command-line arguments and delegates execution to the stage controller.
"""
from __future__ import annotations

import argparse
import sys

from .config import setup_logging
from .stages import run_experiments


def main() -> None:
    """
    Main entry point. 
    Initializes logging, parses arguments, and starts the experiment runner.
    """
    # 1. Initialize logging configuration (CRITICAL: Must be called first)
    setup_logging()

    # 2. Define Arguments
    parser = argparse.ArgumentParser(
        description="D-HASH Experiment Runner: Official reproduction script for the paper."
    )

    # Mode Selection
    parser.add_argument(
        "--mode",
        type=str,
        choices=["all", "pipeline", "microbench", "ablation", "zipf", "redistrib"],
        default="all",
        help="Experiment mode to run (default: 'all').",
    )

    # Workload Parameters
    parser.add_argument(
        "--dataset",
        type=str,
        choices=["NASA", "eBay", "ALL"],
        default="ALL",
        help="Target dataset for skewed workload simulation.",
    )
    parser.add_argument(
        "--alpha",
        type=float,
        default=1.5,
        help="Zipfian distribution parameter (alpha) for ablation studies.",
    )
    parser.add_argument(
        "--repeats",
        type=int,
        default=10,
        help="Number of repetitions for each experiment to ensure statistical stability.",
    )

    # D-HASH Specific Hyperparameters
    parser.add_argument(
        "--fixed_window",
        type=int,
        default=None,
        help="Override Window Size (W). Defaults to pipeline size or 500.",
    )
    parser.add_argument(
        "--dhash_T",
        type=int,
        default=None,
        help="Override Hot-key Threshold (T). Default depends on logic (usually max(30, W)).",
    )
    parser.add_argument(
        "--pipeline_for_zipf",
        type=int,
        default=None,
        help="Pipeline batch size (B) for the main Zipf experiment.",
    )

    # Algorithm Selection
    parser.add_argument(
        "--algos",
        type=str,
        choices=["auto", "minimal", "all", "custom"],
        default="auto",
        help="Set of algorithms to compare (auto=CH vs D-HASH vs WCH vs HRW).",
    )
    parser.add_argument(
        "--algos_list",
        type=str,
        default="",
        help="Comma-separated list for --algos custom (e.g., 'ch,dhash').",
    )

    # 3. Parse & Run
    args = parser.parse_args()

    # Display startup banner
    print(f"[*] Starting D-HASH Experiments (Mode: {args.mode})")
    print(f"[*] Dataset: {args.dataset}, Repeats: {args.repeats}")

    try:
        run_experiments(
            mode=args.mode,
            alpha_for_ablation=args.alpha,
            dataset_filter=args.dataset,
            fixed_window=args.fixed_window,
            dhash_T=args.dhash_T,
            pipeline_for_zipf=args.pipeline_for_zipf,
            repeats=args.repeats,
            algos=args.algos,
            algos_list=args.algos_list,
        )
    except KeyboardInterrupt:
        print("\n[!] Experiment interrupted by user.")
        sys.exit(130)
    except Exception as e:
        print(f"\n[X] Critical Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
