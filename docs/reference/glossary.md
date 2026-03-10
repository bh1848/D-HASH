# Glossary

## Overview

This document defines the main terms used in the D-HASH repository.

The definitions here follow the current implementation, not a broader distributed systems textbook.

---

## Terms

### D-HASH

A routing rule built on top of Consistent Hashing.

In this repository, D-HASH changes read routing for hot keys after a fixed threshold is reached.

---

### Consistent Hashing

A hash-based routing method that maps keys to nodes on a ring.

In this repository, it is the base routing structure for D-HASH and one of the benchmark baselines.

---

### Weighted Consistent Hashing

A weighted variant of hash-based routing.

It is implemented as a comparison baseline in the experiment layer.

---

### Rendezvous Hashing

A hash-based routing method that selects the highest-scoring node for a key.

It is also implemented as a comparison baseline in the experiment layer.

---

### Primary Node

The default node chosen for a key by the base hash strategy.

Writes always go to the primary node in the current D-HASH implementation.

---

### Alternate Node

A second node assigned to a hot key after the threshold is reached.

In this repository, the alternate is selected deterministically from the ring order.

---

### Hot Key

A key whose read count has reached or passed the configured threshold `T`.

Hot keys are eligible for alternate read routing.

---

### Threshold (`T`)

The per-key read count required before alternate routing is considered.

If a key stays below this threshold, reads continue to use the primary node only.

---

### Guard Phase

A fixed period after the threshold where reads still go to the primary node.

This is implemented before the alternating window rule begins.

---

### Window (`W`)

The fixed count-based window size used after the guard phase.

Reads switch between the primary node and the alternate node in windows of size `W`.

---

### Read Count

The per-key counter used by D-HASH to decide whether the threshold and window rules apply.

This is count-based state, not measured node load.

---

### Dataset

The source workload used by the experiment runner.

The current dataset names are:

- `nasa`
- `ebay`

---

### Benchmark Runner

The code in `dhash_repro` that loads workloads, runs experiments, and writes output files.

---

### Reproduction

Running the implemented benchmark flow again under the same repository setup.

In this project, reproduction means running the same code path with the same modes and comparable inputs.

---

## Scope

This glossary only covers terms used directly in the repository and its documentation.
