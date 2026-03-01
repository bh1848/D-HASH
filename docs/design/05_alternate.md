# 05. Alternate

## Role

The alternate module selects a secondary node
when guard logic allows deviation from primary routing.

It operates after primary resolution
and guard eligibility confirmation.

Alternate selection does not execute
unless the guard permits routing adjustment.

---

## Execution Position

For each eligible request:

1. The primary node is already determined.
2. Guard logic allows alternate consideration.
3. Alternate selection computes a candidate node.
4. The selected candidate is passed to window logic.

If alternate selection fails to produce a valid candidate,
routing falls back to the primary node.

---

## Input and Output

Input:

- Key
- Primary node
- Current node set
- Hashing structure

Output:

- A physical node different from the primary,
  if available.

The module does not update statistics
and does not apply temporal stabilization.

---

## Virtual and Physical Nodes

Ring-based hashing may use virtual nodes.

Primary resolution operates at the virtual node level
but resolves to a physical node.

Alternate selection must consider physical identity.

Selecting another virtual position that maps
to the same physical node does not change load distribution.

Therefore, alternate candidates must differ
at the physical node level.

---

## Responsibility Boundary

Alternate logic:

- Computes candidate nodes
- Avoids selecting the primary physical node
- Does not evaluate guard conditions
- Does not maintain window state
- Does not modify hashing configuration

Guard determines eligibility.
Window determines stability.
Alternate determines the candidate.

Each module has a distinct responsibility.
