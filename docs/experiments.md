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
- `zipf`
- `ablation`
- `all`

### `pipeline`

Runs a pipeline benchmark with the selected dataset.

This mode compares:

- Consistent Hashing
- D-HASH

It also sweeps a small range of Zipf alpha values during request generation.

---

### `zipf`

Runs a synthetic Zipf benchmark across multiple routing strategies.

This mode compares:

- Consistent Hashing
- Weighted Consistent Hashing
- Rendezvous Hashing
- D-HASH

The alpha values for this mode are defined in code.

---

### `ablation`

Runs threshold ablation for D-HASH.

This mode changes the threshold configuration and measures how the D-HASH behavior changes as the hot-key threshold moves.

It does not compare multiple routing families.
It focuses on D-HASH only.

---

### `all`

Runs all experiment stages in sequence.

This is the default mode used for a full benchmark run.

---

## Workloads

The experiment runner supports two dataset names:

- `nasa`
- `ebay`

These workloads are used to generate request traces for benchmark execution.

In addition to dataset-based execution, the repository also includes synthetic Zipf-based evaluation.

---

## What Is Compared

The experiment layer compares routing behavior at the level of:

- request distribution
- throughput
- hotspot concentration
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
