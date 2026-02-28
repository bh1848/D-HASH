from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

import numpy as np

from benchmarks.generators.zipf import sample_zipf_keys


@dataclass(frozen=True)
class Workload:
    """
    Workload spec for client-side routing benchmarks.

    - kind: "zipf" only (for now)
    - read_ratio: fraction of ops that are reads. writes go to primary by design.
    - pipeline: batch size; used only to weight percentile aggregation
      (avg latency per batch with weight=batch_size).
    """

    name: str
    kind: str
    num_ops: int
    num_keys: int
    alpha: float
    read_ratio: float
    pipeline: int
    seed: int


def build_zipf_workload(
    *,
    alpha: float,
    num_ops: int,
    num_keys: int,
    read_ratio: float,
    pipeline: int,
    seed: int,
    name_prefix: str = "zipf",
) -> Workload:
    name = f"{name_prefix}_a{alpha}_ops{num_ops}_keys{num_keys}_r{read_ratio}_p{pipeline}_s{seed}"
    return Workload(
        name=name,
        kind="zipf",
        num_ops=int(num_ops),
        num_keys=int(num_keys),
        alpha=float(alpha),
        read_ratio=float(read_ratio),
        pipeline=max(1, int(pipeline)),
        seed=int(seed),
    )


def materialize_ops(w: Workload) -> tuple[list[str], list[str]]:
    """
    Returns (keys, ops) list aligned by index.
    ops[i] is "read" or "write".
    """
    rng = np.random.default_rng(w.seed)
    keys = sample_zipf_keys(
        rng=rng,
        alpha=w.alpha,
        num_keys=w.num_keys,
        num_ops=w.num_ops,
        key_prefix="k",
    )

    # draw read/write ops with given ratio (deterministic w.r.t seed)
    rw = rng.random(w.num_ops)
    ops = ["read" if x < w.read_ratio else "write" for x in rw.tolist()]
    return keys, ops


def iter_batches(
    keys: list[str], ops: list[str], batch_size: int
) -> Iterable[tuple[list[str], list[str]]]:
    """
    Yields batches of (keys, ops) with fixed batch_size except last.
    """
    n = len(keys)
    bs = max(1, int(batch_size))
    for i in range(0, n, bs):
        yield keys[i : i + bs], ops[i : i + bs]
