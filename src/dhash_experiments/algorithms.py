"""
Core Hashing Algorithms Implementation.

This module contains the implementation of standard hashing algorithms
(Consistent Hashing, Weighted CH, Rendezvous) and the proposed D-HASH algorithm.
"""
from __future__ import annotations

from bisect import bisect
from typing import Any, Dict, List, Optional

try:
    import xxhash as _xx
except ImportError as e:
    raise RuntimeError("The 'xxhash' package is required. Install it via: pip install xxhash") from e

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

    def __init__(self, nodes: List[str], replicas: int = REPLICAS) -> None:
        self.replicas = replicas
        self.ring: Dict[int, str] = {}
        self.sorted_keys: List[int] = []
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
            nodes: List[str],
            weights: Optional[Dict[str, float]] = None,
            base_replicas: int = REPLICAS,
    ) -> None:
        self.base_replicas = base_replicas
        self.weights = weights or {n: 1.0 for n in nodes}
        self.ring: Dict[int, str] = {}
        self.sorted_keys: List[int] = []
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

    def __init__(self, nodes: List[str]) -> None:
        self.nodes = list(nodes)

    @staticmethod
    def _score(key: Any, node: str) -> int:
        # Combine key and node to generate a deterministic score
        return fast_hash64(f"{key}|{node}")

    def get_node(self, key: Any, op: str = "read") -> str:
        if not self.nodes:
            raise ValueError("No nodes available.")

        best_node: Optional[str] = None
        best_score = -1

        # O(N) scan to find the highest score
        for n in self.nodes:
            s = self._score(key, n)
            if s > best_score:
                best_score = s
                best_node = n

        assert best_node is not None
        return best_node


# =============================================================================
# [CORE ALGORITHM] D-HASH (Proposed Method)
# =============================================================================
class DHash:
    """
    Dynamic Hot-key Aware Scalable Hashing (D-HASH).

    This algorithm extends Consistent Hashing by dynamically offloading 
    'read' traffic for hot-keys to alternate nodes using a sticky-window mechanism.

    Attributes:
        nodes (List[str]): List of available physical nodes.
        T (int): Hot-key threshold. Keys exceeding this access count are promoted.
        W (int): Window size. Determines the switching epoch duration.
        reads (Dict): Local counter for key access frequency (Client-side).
        alt (Dict): Mapping for keys promoted to hot status.
        ch (ConsistentHashing): Underlying CH ring for primary routing.
    """

    # Memory optimization: D-HASH maintains counters for many keys.
    __slots__ = ("nodes", "T", "W", "reads", "alt", "ch", "hot_key_threshold")

    def __init__(
            self,
            nodes: List[str],
            hot_key_threshold: int = 50,
            window_size: int = 500,
            replicas: int = REPLICAS,
            ring: Optional[ConsistentHashing] = None,
    ) -> None:
        if not nodes:
            raise ValueError("DHash requires at least one node.")

        self.nodes: List[str] = list(nodes)
        self.T: int = int(hot_key_threshold)
        self.W: int = max(1, int(window_size))

        # Client-side metadata state
        self.reads: Dict[Any, int] = {}
        self.alt: Dict[Any, str] = {}

        # Underlying routing layer
        self.ch = ring if ring is not None else ConsistentHashing(nodes, replicas=replicas)

        # Alias for external access (if needed)
        self.hot_key_threshold: int = self.T

    # --- Internal Helpers ---
    @staticmethod
    def _h(key: Any) -> int:
        return fast_hash64(key)

    def _primary_safe(self, key: Any) -> str:
        """Resolves the Primary Node (P_k) using the underlying CH ring."""
        # Fast-path: access CH internals if possible for speed
        rk = getattr(self.ch, "sorted_keys", None)
        ring = getattr(self.ch, "ring", None)

        if rk and ring:
            hk = self._h(key)
            idx = bisect(rk, hk) % len(rk)
            return ring[rk[idx]]

        # Deterministic fallback if CH interface differs
        return self.nodes[self._h(f"{key}|p") % len(self.nodes)]

    def _ensure_alternate(self, key: Any) -> None:
        """
        Selects an Alternate Node (A_k) for a hot-key.
        Ensures A_k is distinct from P_k using auxiliary hashing.
        """
        if key in self.alt:
            return

        rk = getattr(self.ch, "sorted_keys", None)
        ring = getattr(self.ch, "ring", None)

        if not rk or not ring or len(self.nodes) <= 1:
            # Fallback if cluster is too small
            self.alt[key] = self._primary_safe(key)
            return

        hk = self._h(key)
        i = bisect(rk, hk) % len(rk)
        primary = ring[rk[i]]

        # Use auxiliary hash to find a different node in the ring
        stride_span = max(1, len(self.nodes) - 1)
        stride = 1 + (self._h(f"{key}|alt") % stride_span)

        # 1. Try stride-based selection
        j = i
        for _ in range(len(rk)):
            j = (j + stride) % len(rk)
            cand = ring[rk[j]]
            if cand != primary:
                self.alt[key] = cand
                return

        # 2. Linear scan fallback (rarely hit)
        j = i
        for _ in range(len(rk)):
            j = (j + 1) % len(rk)
            cand = ring[rk[j]]
            if cand != primary:
                self.alt[key] = cand
                return

        self.alt[key] = primary

    # --- Public Routing API ---
    def get_node(self, key: Any, op: str = "read") -> str:
        """
        Routes a request to a node.

        - WRITE: Always routed to Primary Node to maintain consistency.
        - READ: Routed to Primary or Alternate based on hot-status and window epoch.
        """
        # 1. Write Consistency: Always P_k
        if op == "write":
            return self._primary_safe(key)

        # 2. Update Access Counter (Client-side estimation)
        cnt = self.reads.get(key, 0) + 1
        self.reads[key] = cnt

        # 3. Cold Key Check: Route to P_k
        if cnt < self.T and key not in self.alt:
            return self._primary_safe(key)

        # 4. Hot Key Promotion & Guard Phase
        self._ensure_alternate(key)  # Lazy resolution of A_k

        delta = max(0, cnt - self.T)

        # Guard Phase: Stick to P_k for first W requests after promotion
        # to allow A_k cache warm-up.
        if delta < self.W:
            return self._primary_safe(key)

        # 5. Window-based Traffic Switching
        # Epoch 0 (Even) -> Alternate (A_k)
        # Epoch 1 (Odd)  -> Primary (P_k)
        epoch = (delta - self.W) // self.W
        return self.alt[key] if (epoch % 2 == 0) else self._primary_safe(key)
