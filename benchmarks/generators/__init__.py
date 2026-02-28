"""
Workload key generators.

This subpackage contains distribution-based key generators
used by benchmark workloads (e.g., Zipf distribution).

No runtime side-effects.
Only re-exports public generator APIs.
"""

from __future__ import annotations

from .zipf import (
    ZipfSpec,
    make_zipf_pmf,
    sample_zipf_keys,
    topk_expected_mass,
)

__all__ = [
    "ZipfSpec",
    "make_zipf_pmf",
    "sample_zipf_keys",
    "topk_expected_mass",
]
