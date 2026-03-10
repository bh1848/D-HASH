# Paper Alignment

## Overview

This repository is a reproduction of the D-HASH paper at the level of routing structure and experiment intent.

The goal of this document is to explain what is aligned with the paper and what is not.

It should not be read as a claim of exact artifact equivalence.

---

## Alignment Goal

The implementation keeps the main idea of the paper:

- start from **Consistent Hashing**
- identify hot keys using a threshold
- introduce alternate routing for hot reads
- keep the routing rule bounded instead of always redirecting traffic

This repository is aligned with the paper in that sense.

---

## What Is Implemented

The current code implements D-HASH as a deterministic routing rule with the following behavior:

- writes go to the primary node
- reads are counted per key
- once a key passes threshold `T`, one alternate node is assigned
- after a guard phase, reads switch between the primary node and the alternate node in fixed windows

This is the concrete interpretation used by the repository.

---

## How This Matches the Paper

The implementation matches the paper at a conceptual level:

### Base Structure

The primary routing path is still hash-based.

### Hot-Key Handling

A key is treated differently only after it becomes hot enough.

### Controlled Alternate Routing

The router does not redirect all traffic immediately.
It introduces alternate routing in a bounded way.

These points are consistent with the main idea of extending hash-based routing for hot-key workloads.

---

## What This Repository Does Not Claim

This repository does not claim:

- exact equivalence with the original research artifact
- the same internal constants in every environment
- the same infrastructure setup as the paper
- the same benchmark numbers on every machine
- real-time load measurement or dynamic node optimization

The current implementation is simpler than a full production-grade system and should be read that way.

---

## Practical Reading of Alignment

In this project, paper alignment means:

> the repository preserves the core routing idea and evaluates it in a reproducible benchmark setup.

That is enough for this codebase, because the goal is to make the implementation clear and testable rather than to reproduce every surrounding detail of the original environment.

---

## Scope

This document describes conceptual and implementation-level alignment.

Detailed benchmark procedures and result files are documented separately in the reproduction documents.
