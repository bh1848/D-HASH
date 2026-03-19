# Experiments

## Overview

This repository evaluates D-HASH in a Redis-based benchmark environment.

The experiment code is organized around a small number of benchmark modes.
Each mode answers a different question about the routing behavior.

The purpose of these experiments is not to simulate a full production system.
The purpose is to compare routing strategies under controlled workloads.

---

## Experiment Modes

The current implementation supports the following modes:

- `pipeline`
- `microbench`
- `zipf`
- `ablation`
- `redistrib`
- `all`

### `pipeline`

Runs a pipeline benchmark with the selected dataset.

This mode compares:

- Consistent Hashing
- D-HASH

It sweeps pipeline sizes `B ∈ {50, 100, 200, 500, 1000}` using a Zipf workload with `alpha = 1.5`.

---

### `microbench`

Runs routing-only microbenchmarks for:

- Consistent Hashing
- D-HASH (cold path)
- D-HASH (hot path)

This mode measures pure `get_node()` overhead in `ns/op` without Redis I/O.

---

### `zipf`

Runs a Zipf benchmark across multiple routing strategies.

This mode compares:

- Consistent Hashing
- Weighted Consistent Hashing
- Rendezvous Hashing
- D-HASH

The benchmark runner generates Zipf-distributed request sequences from dataset-derived key bases.

The alpha values for this mode are defined in code by default.
They may also be overridden at runtime with `DHASH_ZIPF_ALPHAS`.

---

### `ablation`

Runs threshold ablation for D-HASH.

This mode changes the threshold configuration and measures how the D-HASH behavior changes as the hot-key threshold moves.

It does not compare multiple routing families.
It focuses on D-HASH only.

---

### `all`

Runs `pipeline`, `microbench`, `zipf`, and `ablation` in sequence.

This is the default mode used for a full benchmark run.

---

### `redistrib`

Runs an offline redistribution report for membership changes.

This mode compares:

- Consistent Hashing
- Weighted Consistent Hashing
- Rendezvous Hashing

It evaluates `5 -> 6` and `6 -> 5` node changes using up to 100,000 sampled keys.

---

## Workloads

The experiment runner supports two dataset names:

- `nasa`
- `ebay`

These workloads are used to generate request traces for benchmark execution.

The benchmark runner generates Zipf-distributed request sequences from these dataset-derived key bases.

---

## What Is Compared

The experiment layer compares routing behavior at the level of:

- request distribution
- throughput
- latency
- load stddev
- redistribution rate
- changes across repeated runs

The comparison is intentionally narrow.
It is focused on routing behavior, not system operations.

---

## Runtime Environment

Experiments run in a Docker-based Redis environment.

```text
Runner Container → Routing Strategy → Redis Nodes
```

The runner creates the selected strategy, loads the configured workload, sends requests, and writes result files.

---

## Repeated Runs

The environment variable `DHASH_REPEATS` controls how many times a benchmark is repeated.

Repeated execution is used to reduce one-off noise and make comparisons easier.

The implementation uses different random seeds across repeated runs.

---

## Scope

These experiments are designed for reproduction and comparison.

They do not attempt to model:

- cluster membership changes
- node failures
- service discovery
- live operational recovery
- real-time routing from measured node load

The scope is smaller: run the implemented routing rules against controlled workloads and compare the outputs.
