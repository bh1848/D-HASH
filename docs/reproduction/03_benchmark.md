# Benchmark

## Overview

This document describes how the benchmark is executed in the current repository.

The benchmark runner is responsible for loading a workload, selecting a routing strategy, sending requests to Redis nodes, and writing result files.

---

## Benchmark Flow

The benchmark process is:

1. select an experiment mode
2. load the dataset or synthetic workload
3. create the routing strategy
4. run requests against Redis nodes
5. record outputs

This flow is the same in all benchmark modes, although the compared strategies and parameter sweeps differ.

---

## Benchmark Modes

### Pipeline

The pipeline benchmark compares:

- Consistent Hashing
- D-HASH

This mode runs against the selected dataset and sweeps a range of Zipf alpha values used in request generation.

---

### Zipf

The Zipf benchmark compares:

- Consistent Hashing
- Weighted Consistent Hashing
- Rendezvous Hashing
- D-HASH

This mode uses synthetic Zipf workloads defined in code.

---

### Ablation

The ablation benchmark runs D-HASH under multiple threshold values.

This is used to see how the threshold changes the routing result.

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
- distribution across nodes
- hotspot concentration
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
