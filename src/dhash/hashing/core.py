from bisect import bisect
from typing import Any, Dict, List, Optional

try:
    import xxhash as _xx
except ImportError as e:
    raise RuntimeError(
        "The 'xxhash' package is required. Install it via: pip install xxhash"
    ) from e

from ..config import REPLICAS


def fast_hash64(key: Any) -> int:
    return int(_xx.xxh64(str(key).encode("utf-8")).intdigest())


class ConsistentHashing:
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
        for i in range(self.replicas):
            k = self._hash(f"{node}:{i}")
            self.ring[k] = node
            self.sorted_keys.append(k)
        self.sorted_keys.sort()

    def get_node(self, key: Any, op: str = "read") -> str:
        if not self.ring:
            raise ValueError("Ring is empty. Add nodes first.")
        hk = self._hash(key)
        idx = bisect(self.sorted_keys, hk) % len(self.sorted_keys)
        return self.ring[self.sorted_keys[idx]]


class WeightedConsistentHashing:
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
        if not self.weights:
            return
        total_points = len(self.weights) * self.base_replicas
        wsum = sum(self.weights.values()) or 1.0
        quotas = {n: (w / wsum) * total_points for n, w in self.weights.items()}
        floors = {n: int(q) for n, q in quotas.items()}
        remain = total_points - sum(floors.values())
        order = sorted(self.weights.keys(), key=lambda n: (quotas[n] - floors[n], n), reverse=True)
        alloc = floors.copy()
        for n in order[: int(remain)]:
            alloc[n] += 1
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


class RendezvousHashing:
    def __init__(self, nodes: List[str]) -> None:
        self.nodes = list(nodes)

    @staticmethod
    def _score(key: Any, node: str) -> int:
        return fast_hash64(f"{key}|{node}")

    def get_node(self, key: Any, op: str = "read") -> str:
        if not self.nodes:
            raise ValueError("No nodes available.")
        best_node: Optional[str] = None
        best_score = -1
        for n in self.nodes:
            s = self._score(key, n)
            if s > best_score:
                best_score = s
                best_node = n
        assert best_node is not None
        return best_node
