# 02. Hashing

## Role

The hashing layer provides deterministic key-to-node mapping.

It resolves the primary node for a given key.
No routing condition or runtime traffic state influences this step.

---

## Location

Implementation:

`src/dhash/hashing/`

This module contains:

- Consistent hashing
- Weighted consistent hashing
- Rendezvous hashing
- `fast_hash64` utility

Each strategy maps a key to a single primary node.

---

## Primary Resolution

For a request key:

1. The key is converted into a 64-bit hash value.
2. The hash value is used by the selected hashing strategy.
3. A primary node is deterministically selected.

The result depends only on:

- Node membership
- Replica configuration
- Hash function

Given identical configuration,
the same key resolves to the same primary node.

---

## Virtual Nodes

Ring-based hashing strategies use virtual nodes.

Each physical node may correspond to multiple positions
depending on replica configuration.

Primary selection operates on the virtual ring
but resolves to a physical node.

This distinction becomes relevant during alternate selection.

---

## Boundary with Routing

Hashing:

- Computes primary node
- Does not evaluate hot-key status
- Does not apply guard logic
- Does not select alternates
- Does not maintain runtime statistics

Routing logic executes after primary resolution.

Hashing remains the baseline mapping layer.
