from typing import Any

import pytest

from dhash.config import VIRTUAL_POINTS_PER_NODE
from dhash.hashing.core import (
    ConsistentHashing,
    RendezvousHashing,
    WeightedConsistentHashing,
    fast_hash64,
)


@pytest.mark.parametrize("key", ["key1", "test_key", 12345])
def test_fast_hash64_is_deterministic(key: Any) -> None:
    assert fast_hash64(key) == fast_hash64(key)


@pytest.mark.parametrize(
    "algo",
    [
        ConsistentHashing(["node1", "node2", "node3"]),
        WeightedConsistentHashing(["node1", "node2", "node3"]),
        RendezvousHashing(["node1", "node2", "node3"]),
    ],
)
def test_hashing_algorithms_route_to_known_nodes(algo: Any) -> None:
    node = algo.get_node("test_key")
    assert node in {"node1", "node2", "node3"}


def test_consistent_hashing_uses_virtual_points_default() -> None:
    algo = ConsistentHashing(["node1", "node2"])

    assert algo.replicas == VIRTUAL_POINTS_PER_NODE
    assert len(algo.sorted_keys) == 2 * VIRTUAL_POINTS_PER_NODE
