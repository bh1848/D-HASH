# Benchmark

## Overview

This document describes how the benchmark is executed in the current repository.

The benchmark runner is responsible for loading a workload, selecting a routing strategy, sending requests to Redis nodes, and writing result files.

---

## Benchmark Flow

The benchmark process is:

1. select an experiment mode
2. load the dataset base or create the requested benchmark key set
3. create the routing strategy
4. flush Redis databases
5. preload controlled-initialization data when needed
6. warm up sampled keys
7. run the measured benchmark phase
8. record outputs

This flow is the same in all benchmark modes, although the compared strategies and parameter sweeps differ.

---

## Benchmark Modes

### Pipeline

The pipeline benchmark compares:

- Consistent Hashing
- D-HASH

This mode runs against the selected dataset and sweeps pipeline sizes `B ∈ {50, 100, 200, 500, 1000}` using `alpha = 1.5`.

### Microbench

This stage measures pure routing overhead in `ns/op` and does not execute Redis I/O.

It compares:

- CH cold path
- D-HASH cold path
- D-HASH hot path

---

### Zipf

The Zipf benchmark compares:

- Consistent Hashing
- Weighted Consistent Hashing
- Rendezvous Hashing
- D-HASH

This mode uses dataset-derived key bases and applies the default alpha sweep defined in code.
The sweep may also be overridden with `DHASH_ZIPF_ALPHAS`.

---

### Ablation

The ablation benchmark runs D-HASH under multiple threshold values.

This is used to see how the threshold changes the routing result.

### Redistribution

This stage computes offline move rates for membership changes.

It compares:

- Consistent Hashing
- Weighted Consistent Hashing
- Rendezvous Hashing

It evaluates `5 -> 6` and `6 -> 5` node mappings using up to 100,000 sampled keys.

---

## Execution Environment

The benchmark is designed to run in Docker with multiple Redis containers and one runner container.

```text
Workload → Runner → Routing Strategy → Redis Nodes
```

This is a controlled benchmark setup, not a production deployment model.

---

## What The Benchmark Measures

The benchmark output is used to compare routing strategies at the level of:

- throughput
- average latency
- tail latency
- load stddev
- redistribution rate
- differences between repeated runs

The exact result files are described in the results format document.

---

## Scope

This benchmark is intended to evaluate the implemented routing logic.

It does not attempt to reproduce:

- production network behavior
- failover handling
- live node health decisions
- cluster resizing during execution
