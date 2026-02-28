"""
Core Hashing Algorithms Implementation.

This module contains the implementation of standard hashing algorithms
(Consistent Hashing, Weighted CH, Rendezvous).
"""

from __future__ import annotations

from bisect import bisect
from typing import Any

try:
    import xxhash as _xx
except ImportError as e:
    raise RuntimeError(
        "The 'xxhash' package is required. Install it via: pip install xxhash"
    ) from e

from .config import REPLICAS


# -----------------------------------------------------------------------------
# Utility: Fast Hash Function
# -----------------------------------------------------------------------------
def fast_hash64(key: Any) -> int:
    """Computes a 64-bit non-cryptographic hash using xxHash."""
    return _xx.xxh64(str(key).encode("utf-8")).intdigest()


# -----------------------------------------------------------------------------
# Baseline 1: Consistent Hashing (CH)
# -----------------------------------------------------------------------------
class ConsistentHashing:
    """
    Standard Consistent Hashing implementation using a virtual node ring.

    Attributes:
        replicas (int): Number of virtual nodes per physical node.
        ring (Dict[int, str]): Mapping of hash values to node names.
        sorted_keys (List[int]): Sorted list of hash values on the ring.
    """

    def __init__(self, nodes: list[str], replicas: int = REPLICAS) -> None:
        self.replicas = replicas
        self.ring: dict[int, str] = {}
        self.sorted_keys: list[int] = []
        for node in nodes:
            self.add_node(node)

    @staticmethod
    def _hash(key: Any) -> int:
        return fast_hash64(key)

    def add_node(self, node: str) -> None:
        """Adds a new node to the hash ring with virtual replicas."""
        for i in range(self.replicas):
            k = self._hash(f"{node}:{i}")
            self.ring[k] = node
            self.sorted_keys.append(k)
        self.sorted_keys.sort()

    def get_node(self, key: Any, op: str = "read") -> str:
        """Resolves the target node for a given key."""
        if not self.ring:
            raise ValueError("Ring is empty. Add nodes first.")

        hk = self._hash(key)
        # Binary search for the first node clockwise
        idx = bisect(self.sorted_keys, hk) % len(self.sorted_keys)
        return self.ring[self.sorted_keys[idx]]


# -----------------------------------------------------------------------------
# Baseline 2: Weighted Consistent Hashing (WCH)
# -----------------------------------------------------------------------------
class WeightedConsistentHashing:
    """
    Consistent Hashing with capacity-aware weights.
    Nodes with higher weights are assigned more virtual slots on the ring.
    """

    def __init__(
        self,
        nodes: list[str],
        weights: dict[str, float] | None = None,
        base_replicas: int = REPLICAS,
    ) -> None:
        self.base_replicas = base_replicas
        self.weights = weights or {n: 1.0 for n in nodes}
        self.ring: dict[int, str] = {}
        self.sorted_keys: list[int] = []
        self._build_ring()

    @staticmethod
    def _hash(key: Any) -> int:
        return fast_hash64(key)

    def _build_ring(self) -> None:
        """Distributes virtual nodes based on normalized weights."""
        if not self.weights:
            return

        total_points = len(self.weights) * self.base_replicas
        wsum = sum(self.weights.values()) or 1.0

        # Calculate quota per node
        quotas = {n: (w / wsum) * total_points for n, w in self.weights.items()}
        floors = {n: int(q) for n, q in quotas.items()}

        # Distribute remaining points by largest remainder
        remain = total_points - sum(floors.values())
        order = sorted(
            self.weights.keys(),
            key=lambda n: (quotas[n] - floors[n], n),
            reverse=True,
        )

        alloc = floors.copy()
        for n in order[: int(remain)]:
            alloc[n] += 1

        # Place nodes on the ring
        for node, reps in alloc.items():
            for i in range(reps):
                k = self._hash(f"{node}:{i}")
                self.ring[k] = node
                self.sorted_keys.append(k)
        self.sorted_keys.sort()

    def get_node(self, key: Any, op: str = "read") -> str:
        if not self.ring:
            raise ValueError("Ring is empty.")
        hk = self._hash(key)
        idx = bisect(self.sorted_keys, hk) % len(self.sorted_keys)
        return self.ring[self.sorted_keys[idx]]


# -----------------------------------------------------------------------------
# Baseline 3: Rendezvous Hashing (HRW)
# -----------------------------------------------------------------------------
class RendezvousHashing:
    """
    Rendezvous (Highest Random Weight) Hashing.
    Selects the node that yields the highest hash score for a given key.
    """

    def __init__(self, nodes: list[str]) -> None:
        self.nodes = list(nodes)

    @staticmethod
    def _score(key: Any, node: str) -> int:
        # Combine key and node to generate a deterministic score
        return fast_hash64(f"{key}|{node}")

    def get_node(self, key: Any, op: str = "read") -> str:
        if not self.nodes:
            raise ValueError("No nodes available.")

        best_node: str | None = None
        best_score = -1

        # O(N) scan to find the highest score
        for n in self.nodes:
            s = self._score(key, n)
            if s > best_score:
                best_score = s
                best_node = n

        assert best_node is not None
        return best_node
