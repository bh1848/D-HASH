# 01. Overview

## Purpose

D-HASH is a client-side routing layer built on top of hashing-based key distribution.

It addresses node-level imbalance caused by hot-keys
while preserving deterministic hashing as the baseline mapping.

The storage layer remains unchanged.

---

## System Structure

The system is divided into two layers:

- **Hashing layer** (`src/dhash/hashing/`)
- **Routing layer** (`src/dhash/routing/`)

Hashing determines the primary node.
Routing may conditionally override that decision.

---

## Routing Composition

The routing layer consists of:

- `router` — execution control
- `guard` — eligibility evaluation
- `alternate` — alternate node selection
- `window` — temporal stabilization
- `stats` — runtime statistics

Each module has a single responsibility.

---

## Execution Flow

For each request:

1. Compute primary node via hashing.
2. Update runtime statistics.
3. Evaluate guard conditions.
4. If allowed, select alternate node.
5. Apply window stabilization.
6. Return final target node.

Hashing provides the baseline.
Routing introduces conditional deviation.

---

## Design Characteristics

- Deterministic primary mapping
- Adaptive routing under controlled conditions
- Explicit module boundaries
- Reproducible execution behavior
