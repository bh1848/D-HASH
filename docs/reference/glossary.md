# Glossary

This document defines structural terms used in D-HASH.

Definitions describe responsibility boundaries only.

---

## Primary

The node returned by the hashing layer for a given key.

Resolved before any routing adjustment.

---

## Alternate

A node selected by the alternate module
when guard eligibility is satisfied.

Alternate selection does not modify hashing state.

---

## Guard

A routing component that evaluates
whether alternate routing is allowed.

Produces an eligibility decision.

---

## Window

A routing mechanism that maintains
per-key temporal routing state.

Controls reuse of previously selected alternates.

---

## Virtual Node

A logical ring position associated
with a physical node in ring-based hashing.

Multiple virtual nodes may map
to one physical node.

---

## Physical Node

The actual routing target returned by the router.

---

## Runtime Statistics

Per-key access state maintained by `stats`.

Used by guard logic during eligibility evaluation.

---

## Reproduction Layer

The experiment execution layer
implemented under `src/dhash_repro/`.

Separate from the core routing path.
