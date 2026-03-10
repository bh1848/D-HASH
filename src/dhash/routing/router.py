from bisect import bisect
from typing import Any, Dict, List, Optional, Tuple, cast

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
        self._ring_signature: Tuple[Tuple[int, ...], Tuple[str, ...]] = (
            self._compute_ring_signature()
        )

    @staticmethod
    def _h(key: Any) -> int:
        return fast_hash64(key)

    def _compute_ring_signature(self) -> Tuple[Tuple[int, ...], Tuple[str, ...]]:
        rk = tuple(getattr(self.ch, "sorted_keys", []))
        ring = cast(Dict[int, str], getattr(self.ch, "ring", {}))
        owners = tuple(ring[k] for k in rk)
        return rk, owners

    def _current_ring_nodes(self) -> List[str]:
        ring = cast(Dict[int, str], getattr(self.ch, "ring", {}))
        ordered: List[str] = []
        seen = set()
        for k in getattr(self.ch, "sorted_keys", []):
            node = ring[k]
            if node not in seen:
                seen.add(node)
                ordered.append(node)
        return ordered or list(self.nodes)

    def _sync_membership_if_needed(self) -> None:
        signature = self._compute_ring_signature()
        if signature == self._ring_signature:
            return
        self._ring_signature = signature
        self.nodes = self._current_ring_nodes()
        self.alt.clear()

    def refresh_membership(self, nodes: List[str]) -> None:
        self.nodes = list(nodes)
        self.ch = ConsistentHashing(self.nodes, replicas=self.ch.replicas)
        self.alt.clear()
        self._ring_signature = self._compute_ring_signature()

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
