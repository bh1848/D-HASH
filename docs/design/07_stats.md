# 07. Stats

## Role

The stats module maintains runtime access statistics.

It provides traffic-related information
used by the routing layer to evaluate eligibility conditions.

Statistics are updated per request
before guard evaluation.

---

## Location

Implementation:

`src/dhash/stats.py`

This module is part of the core library,
not the reproduction layer.

---

## Responsibility

The stats module:

- Records per-key access information
- Maintains traffic-related counters or measurements
- Provides data required by guard logic

It does not:

- Resolve primary nodes
- Select alternate nodes
- Apply window stabilization
- Execute experiments
- Persist benchmark results

---

## Execution Position

For each request:

1. Primary node is resolved.
2. Statistics are updated.
3. Guard logic reads statistical state.
4. Routing decision proceeds.

Statistics update occurs before guard evaluation.

---

## Boundary with Reproduction Layer

The stats module operates inside the core routing path.

The reproduction layer (`src/dhash_repro/`)
collects experiment-level metrics and writes results.

Runtime statistics used for routing decisions
are separate from benchmark aggregation logic.

---

## Design Characteristic

Statistics are maintained locally within the routing process.

They influence routing eligibility
but do not alter hashing behavior directly.

All adaptive decisions remain controlled
by the routing layer.
