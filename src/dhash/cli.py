"""
Command-line interface for D-HASH experiments.

This file is a direct move of the previous cli entrypoint.
No algorithmic logic is modified here.
"""

from __future__ import annotations

import argparse

from .config import setup_logging
from .routing import DHash
from .utils.time import now_ns


def main() -> None:
    setup_logging()

    parser = argparse.ArgumentParser(prog="dhash")
    parser.add_argument("--mode", choices=["route", "noop"], default="route")
    parser.add_argument("--key", type=str)
    parser.add_argument("--op", type=str, default="read")
    parser.add_argument("--threshold", type=int, default=50)
    parser.add_argument("--window", type=int, default=500)

    args = parser.parse_args()

    if args.mode == "route":
        if not args.key:
            raise ValueError("Key is required for routing mode.")

        nodes = [f"redis-{i}" for i in range(1, 6)]
        router = DHash(
            nodes=nodes,
            hot_key_threshold=args.threshold,
            window_size=args.window,
        )

        start = now_ns()
        node = router.get_node(args.key, op=args.op)
        end = now_ns()

        print(f"{args.op} {args.key} -> {node}")
        print(f"latency_ns={end - start}")

    else:
        print("No operation selected.")


if __name__ == "__main__":
    main()
