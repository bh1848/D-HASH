# 03. Results Format

This document describes experiment output structure.

Result generation is handled by the reproduction layer.

---

## Output Scope

Results may include:

- Per-node request distribution
- Routing decision statistics
- Aggregated imbalance indicators

The exact format is defined by the persistence module
within `src/dhash_repro/`.

---

## Separation from Core

The reproduction layer:

- Executes experiments
- Collects benchmark-level metrics
- Persists result data

It does not modify:

- Hashing logic
- Guard logic
- Alternate selection
- Window behavior
- Runtime statistics implementation

Core routing behavior remains unchanged during benchmarking.
