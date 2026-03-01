# 04. Guard

## Role

The guard determines whether a key is eligible
for alternate routing.

It separates:

- Primary-only routing
- Conditional routing adjustment

Guard logic executes after primary resolution
and statistics update.

---

## Execution Position

For each request:

1. Primary node is resolved.
2. Access statistics are updated.
3. Guard conditions are evaluated.
4. If the guard denies eligibility,
   the primary node remains the final target.
5. If the guard allows eligibility,
   alternate selection may proceed.

Guard does not select nodes.
It only evaluates eligibility.

---

## Responsibility

The guard evaluates runtime state,
including traffic-related conditions.

Its output is binary:

- Not eligible → retain primary
- Eligible → allow alternate consideration

It does not:

- Modify hashing state
- Select alternate nodes
- Apply window stabilization
- Maintain routing history

---

## Boundary

Guard logic defines when routing may deviate
from deterministic hashing.

Alternate selection and window stabilization
operate only if guard allows eligibility.

Hashing remains the baseline mapping layer.
The router enforces execution order.
