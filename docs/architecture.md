# Architecture

## Overview

This repository is organized into two layers:

- **`dhash`**: core routing library
- **`dhash_repro`**: experiment runner

The `dhash` package contains the hashing and routing logic.
The `dhash_repro` package loads workloads, runs experiments, and writes benchmark results.

This split keeps the routing code separate from dataset handling and experiment execution.

---

## Core Library (`src/dhash`)

The `dhash` package implements the routing behavior used in the experiments.

Its main responsibilities are:

- building the hash ring
- selecting the primary node
- applying the D-HASH read rule
- storing lightweight per-key routing state

This layer does not load datasets or manage benchmark output.

---

## Hashing Layer

The hashing layer provides the hash structures used by the project.

Implemented strategies include:

- Consistent Hashing
- Weighted Consistent Hashing
- Rendezvous Hashing

D-HASH itself uses **Consistent Hashing** as its base structure.

The other strategies are used as comparison baselines in the experiment layer.

---

## Routing Layer

The routing layer contains the D-HASH-specific logic.

### `router.py`

Defines the main `DHash` router.

It keeps:

- the node list
- the hot-key threshold `T`
- the window size `W`
- per-key read counts
- per-key alternate nodes

Writes always go to the primary node.
Reads may switch between the primary node and an alternate node after the threshold is reached.

### `alternate.py`

Computes one alternate node for a key.

The alternate is selected deterministically from the ring order.
It is not chosen from observed node load.

### `guard.py`

Implements the fixed guard phase after the threshold.

During this phase, reads still go to the primary node.

### `window.py`

Implements the count-based window rule after the guard phase.

At that point, reads alternate between the primary node and the alternate node in windows of size `W`.

---

## Experiment Layer (`src/dhash_repro`)

The `dhash_repro` package is responsible for running benchmarks.

Its responsibilities are:

- loading a dataset or trace
- generating request sequences
- running benchmark modes
- comparing routing strategies
- writing result files

This layer is intentionally separate from `dhash` so that the routing code remains small and focused.

---

## Runtime

Experiments are executed in a Docker-based Redis environment.

```text
Runner Container → Router / Hashing Strategy → Redis Nodes
```

The runner selects a workload, creates the routing strategy, sends requests to Redis nodes, and writes benchmark results to the persistence directory.

---

## Request Flow

The current D-HASH request flow is:

### Write

```text
Client Request
      │
      ▼
Primary Node from Consistent Hashing
      │
      ▼
Redis Node
```

### Read

```text
Client Request
      │
      ▼
Read Count Update
      │
      ▼
Primary Node from Consistent Hashing
      │
      ▼
Threshold / Guard / Window Rule
      │
      ▼
Primary or Alternate Node
      │
      ▼
Redis Node
```

The read path depends on per-key count state.
The write path does not.

---

## Design Principle

The main design principle of this repository is separation of concerns.

- routing logic stays in `dhash`
- experiment logic stays in `dhash_repro`

This makes the implementation easier to explain and easier to test.

---

## Scope

This repository is built for experiment reproduction.

It does not try to provide:

- production cluster orchestration
- live node health management
- runtime service discovery
- failover handling
- real-time load-based routing

The goal is narrower: implement the current D-HASH routing rule and evaluate it in a repeatable benchmark environment.
