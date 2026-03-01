# 06. Window

## Role

The window module stabilizes routing decisions over time.

When alternate routing becomes eligible,
the window prevents frequent switching
between primary and alternate nodes.

It introduces temporal consistency
into the routing process.

---

## Execution Position

Window logic executes after:

1. Primary resolution
2. Statistics update
3. Guard eligibility confirmation
4. Alternate candidate computation

The window determines whether:

- A previously selected alternate should be reused
- A new alternate should be applied
- Routing should fall back to primary

---

## Window State

The window maintains per-key routing state.

This state may include:

- Previously selected alternate
- Time or epoch reference
- Validity interval

The state is evaluated on each eligible request.

If the window remains valid,
the previously selected alternate is reused.

If the window expires,
a new alternate may be applied.

---

## Fallback Behavior

If guard denies eligibility:

- The primary node is returned.

If no valid alternate exists:

- The primary node remains the routing result.

Window logic does not override guard decisions.

---

## Responsibility Boundary

The window:

- Does not compute primary nodes
- Does not detect hot-keys
- Does not select alternate candidates
- Does not modify hashing configuration

Guard controls eligibility.
Alternate computes candidates.
Window enforces temporal stability.

Each module operates within its defined boundary.
