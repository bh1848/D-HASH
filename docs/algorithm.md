# Algorithm

## Overview

D-HASH in this repository is implemented as a read-side routing rule on top of **Consistent Hashing**.

The base behavior is simple:

- writes always go to the primary node
- reads start at the primary node
- after a key becomes hot enough, reads may alternate between the primary node and one alternate node

The implementation is based on per-key read counts, a threshold `T`, and a window size `W`.

---

## Base Routing

The base routing structure is **Consistent Hashing**.

For any key, the router first finds a primary node from the hash ring.

```text
key → hash ring → primary node
```

This primary node is always used for writes.

---

## Read Behavior

D-HASH only changes the behavior of reads.

For each read:

1. increment the read count for the key
2. if the count is still below the threshold, return the primary node
3. otherwise, ensure that an alternate node exists for the key
4. select either the primary node or the alternate node based on the current count window

This means the implementation is count-based, not load-based.

---

## Threshold

Each key has a read counter.

Let:

- `cnt` = read count for the key
- `T` = hot-key threshold

If:

```text
cnt < T
```

the router returns the primary node.

Once the count reaches the threshold, the key is treated as hot enough to consider alternate routing.

---

## Alternate Node

The implementation stores at most one alternate node per key.

The alternate node is chosen deterministically from the hash ring order.
It is not selected from measured node load or runtime latency.

In practice, the router:

1. finds the key position on the ring
2. walks forward on the ring
3. collects distinct non-primary nodes
4. picks one using a stride derived from the key hash

This makes alternate selection stable for the same key and ring membership.

---

## Guard Phase

After the threshold is reached, the router does not switch to the alternate immediately.

Let:

- `W` = window size
- `delta = cnt - T`

If:

```text
delta < W
```

the router still returns the primary node.

This acts as a fixed guard phase after the threshold.

---

## Window Rule

After the guard phase, the router alternates between the primary node and the alternate node in windows of size `W`.

The rule is:

- first window after the guard phase: alternate
- next window: primary
- next window: alternate
- and so on

So the read path becomes count-based switching between two nodes.

---

## Request Flow

The routing flow is:

### Write

```text
key → primary node
```

### Read

```text
read count update
      │
      ▼
primary node from hash ring
      │
      ▼
count < T ? ── yes → primary
      │
      no
      ▼
ensure alternate
      │
      ▼
guard phase ? ── yes → primary
      │
      no
      ▼
window rule → primary or alternate
```

---

## What This Implementation Does Not Do

The current implementation does not:

- measure real-time node load
- estimate latency per node
- choose alternates from live performance data
- rebalance writes across multiple nodes

The algorithm in this repository should be read as a deterministic reproduction of the main D-HASH idea, not as a dynamic load balancer.

---

## Scope

This document describes the behavior implemented in the current codebase.

It is intentionally limited to the actual routing logic used by the repository.
