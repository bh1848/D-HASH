from bisect import bisect
from typing import Any, Dict, List, Optional, cast

from ..config import (
    DEFAULT_HOT_KEY_THRESHOLD,
    DEFAULT_WINDOW_SIZE,
    VIRTUAL_POINTS_PER_NODE,
)
from ..hashing.core import ConsistentHashing, fast_hash64
from .alternate import ensure_alternate
from .guard import check_guard_phase
from .window import select_window_route


class DHash:
    __slots__ = (
        "nodes",
        "T",
        "W",
        "reads",
        "alt",
        "ch",
        "hot_key_threshold",
        "_ring_signature",
    )

    def __init__(
        self,
        nodes: List[str],
        hot_key_threshold: int = DEFAULT_HOT_KEY_THRESHOLD,
        window_size: Optional[int] = DEFAULT_WINDOW_SIZE,
        replicas: int = VIRTUAL_POINTS_PER_NODE,
        ring: Optional[ConsistentHashing] = None,
    ) -> None:
        if not nodes:
            raise ValueError("DHash requires at least one node.")
        self.nodes: List[str] = list(nodes)
        self.T: int = int(hot_key_threshold)
        resolved_window = DEFAULT_WINDOW_SIZE if window_size is None else int(window_size)
        self.W: int = max(1, resolved_window)
        self.reads: Dict[Any, int] = {}
        self.alt: Dict[Any, str] = {}
        self.ch = ring if ring is not None else ConsistentHashing(nodes, replicas=replicas)
        self.hot_key_threshold: int = self.T
        self._ring_signature = self._compute_ring_signature()

    @staticmethod
    def _h(key: Any) -> int:
        return fast_hash64(key)

    def _sync_membership_if_needed(self) -> None:
        current_signature = self._compute_ring_signature()
        if current_signature == self._ring_signature:
            return

        self._ring_signature = current_signature
        self.nodes = self._extract_nodes_from_ring()
        self.alt.clear()

    def refresh_membership(self, nodes: List[str]) -> None:
        self.nodes = list(nodes)
        self.ch = ConsistentHashing(self.nodes, replicas=self.ch.replicas)
        self._ring_signature = self._compute_ring_signature()
        self.alt.clear()

    def _extract_nodes_from_ring(self) -> List[str]:
        rk = getattr(self.ch, "sorted_keys", None)
        ring = getattr(self.ch, "ring", None)
        if not rk or not ring:
            return list(self.nodes)
        return list(dict.fromkeys(cast(str, ring[key]) for key in rk))

    def _compute_ring_signature(self) -> tuple[Any, ...]:
        rk = tuple(getattr(self.ch, "sorted_keys", ()))
        ring = getattr(self.ch, "ring", {})
        return rk, tuple(cast(str, ring[key]) for key in rk)

    def _primary_safe(self, key: Any) -> str:
        rk = getattr(self.ch, "sorted_keys", None)
        ring = getattr(self.ch, "ring", None)

        if rk and ring:
            hk = self._h(key)
            idx = bisect(rk, hk) % len(rk)
            return cast(str, ring[rk[idx]])

        fallback_idx = self._h(f"{key}|p") % len(self.nodes)
        return self.nodes[fallback_idx]

    def get_node(self, key: Any, op: str = "read") -> str:
        self._sync_membership_if_needed()

        if op == "write":
            return self._primary_safe(key)

        cnt = self.reads.get(key, 0) + 1
        self.reads[key] = cnt

        if cnt < self.T and key not in self.alt:
            return self._primary_safe(key)

        rk = getattr(self.ch, "sorted_keys", [])
        ring = getattr(self.ch, "ring", {})
        primary = self._primary_safe(key)

        ensure_alternate(key, self.alt, self.nodes, rk, ring, self._h, primary)

        if check_guard_phase(cnt, self.T, self.W):
            return primary

        return select_window_route(cnt, self.T, self.W, primary, self.alt[key])


__all__ = ["DHash"]
