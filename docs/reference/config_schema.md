# Configuration Schema

This document describes configuration elements
used by the D-HASH implementation.

---

## Node Set

Defines the list of physical nodes
participating in hashing and routing.

Used during primary resolution.

---

## Replica Count

Defines the number of virtual nodes
per physical node for ring-based hashing.

Affects ring structure only.

---

## Hashing Strategy

Specifies the hashing implementation:

- Consistent hashing
- Weighted consistent hashing
- Rendezvous hashing

Determines primary node resolution behavior.

---

## Guard Parameters

Defines traffic-related conditions
used to determine alternate eligibility.

Evaluated during routing.

---

## Window Parameters

Defines temporal routing behavior.

Used by the window module
to manage per-key routing stability.

---

## Reproduction Parameters

Used only in the reproduction layer.

Examples:

- Workload skew parameter
- Repeat count
- Experiment mode

Do not affect core routing logic.
