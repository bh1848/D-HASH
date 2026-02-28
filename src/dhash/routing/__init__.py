"""
Routing algorithms (D-HASH).
"""

from __future__ import annotations

from bisect import bisect
from typing import Any, Dict, List, Optional

from ..config import REPLICAS
from ..hashing import ConsistentHashing, fast_hash64
from .alternate import ensure_alternate
from .guard import in_guard_phase
from .window import pick_node_by_window

__all__ = ["DHash"]


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
        nodes: list[str],
        hot_key_threshold: int = 50,
        window_size: int = 500,
        replicas: int = REPLICAS,
        ring: ConsistentHashing | None = None,
    ) -> None:
        if not nodes:
            raise ValueError("DHash requires at least one node.")

        self.nodes: list[str] = list(nodes)
        self.T: int = int(hot_key_threshold)
        self.W: int = max(1, int(window_size))

        # Client-side metadata state
        self.reads: dict[Any, int] = {}
        self.alt: dict[Any, str] = {}

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
        ensure_alternate(self, key)  # same side effects as old self._ensure_alternate

        delta = max(0, cnt - self.T)

        # Guard Phase: Stick to P_k for first W requests after promotion
        # to allow A_k cache warm-up.
        if in_guard_phase(delta, self.W):
            return self._primary_safe(key)

        # 5. Window-based Traffic Switching
        # Epoch 0 (Even) -> Alternate (A_k)
        # Epoch 1 (Odd)  -> Primary (P_k)
        return pick_node_by_window(
            delta=delta,
            W=self.W,
            alt_node=self.alt[key],
            primary_fn=self._primary_safe,
            key=key,
        )
