# 02 Hashing

D-HASH builds on a standard Consistent Hashing ring.

Components:

- Virtual replicas per physical node
- 64-bit hash (xxHash64)
- Sorted ring lookup via bisect

Primary resolution:

- For key k, compute h(k)
- Find first clockwise virtual node
- Map to physical node

Alternate selection uses:

- Auxiliary hash h(k | "alt")
- Stride s(k) in range [1, |N|-1]
- s(k)-th successor on the ring

This preserves determinism and avoids self-selection.
