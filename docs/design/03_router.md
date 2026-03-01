# 03. Router

## Role

The router defines the routing control flow.

It connects hashing, guard logic, alternate selection,
window stabilization, and statistics tracking.

All routing decisions pass through this layer.

---

## Control Flow

For each request:

1. Resolve primary node via hashing.
2. Record access statistics.
3. Evaluate guard conditions.
4. If eligible, consider alternate selection.
5. Apply window stabilization.
6. Return final target node.

The sequence is fixed.
Each step is delegated to its respective module.

---

## Responsibility Boundary

The router:

- Defines execution order
- Transfers state between modules
- Enforces fallback to primary when conditions are not met

It does not:

- Implement hashing logic
- Compute alternate candidates
- Maintain ring structure
- Perform statistical computation internally

---

## Design Characteristic

Hashing provides deterministic mapping.

Routing introduces conditional deviation
under controlled execution flow.

The router separates baseline mapping
from adaptive behavior.
