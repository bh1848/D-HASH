from bisect import bisect
from typing import Any, Dict, List, Optional, cast

from ..config import REPLICAS
from ..hashing.core import ConsistentHashing, fast_hash64
from .alternate import ensure_alternate
from .guard import check_guard_phase
from .window import select_window_route


class DHash:
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
        self.reads: Dict[Any, int] = {}
        self.alt: Dict[Any, str] = {}
        self.ch = ring if ring is not None else ConsistentHashing(nodes, replicas=replicas)
        self.hot_key_threshold: int = self.T

    @staticmethod
    def _h(key: Any) -> int:
        return fast_hash64(key)

    def _primary_safe(self, key: Any) -> str:
        rk = getattr(self.ch, "sorted_keys", None)
        ring = getattr(self.ch, "ring", None)

        # Check if ring attributes exist
        if rk and ring:
            hk = self._h(key)
            idx = bisect(rk, hk) % len(rk)
            # Use cast to ensure str return type for Mypy
            return cast(str, ring[rk[idx]])

        # Fallback routing
        fallback_idx = self._h(f"{key}|p") % len(self.nodes)
        return self.nodes[fallback_idx]

    def get_node(self, key: Any, op: str = "read") -> str:
        if op == "write":
            return self._primary_safe(key)

        cnt = self.reads.get(key, 0) + 1
        self.reads[key] = cnt

        if cnt < self.T and key not in self.alt:
            return self._primary_safe(key)

        rk = getattr(self.ch, "sorted_keys", [])
        ring = getattr(self.ch, "ring", {})

        # 1. Alternate selection
        ensure_alternate(key, self.alt, self.nodes, rk, ring, self._h, self._primary_safe(key))

        # 2. Guard phase check
        if check_guard_phase(cnt, self.T, self.W):
            return self._primary_safe(key)

        # 3. Window routing
        # Use cast for the alternate node retrieved from self.alt
        return select_window_route(cnt, self.T, self.W, self._primary_safe(key), self.alt[key])


__all__ = ["DHash"]
