import pytest
from typing import Any, List, Type, Union
from dhash.hashing.core import (
    ConsistentHashing,
    WeightedConsistentHashing,
    RendezvousHashing,
    fast_hash64,
)


@pytest.mark.parametrize("key", ["key1", "test_key", 12345])
def test_fast_hash64_deterministic(key: Any) -> None:
    """Verify that the hash function produces consistent results for the same input."""
    assert fast_hash64(key) == fast_hash64(key)


@pytest.mark.parametrize(
    "algo_class, nodes",
    [
        (ConsistentHashing, ["node1", "node2", "node3"]),
        (WeightedConsistentHashing, ["node1", "node2", "node3"]),
        (RendezvousHashing, ["node1", "node2", "node3"]),
    ],
)
def test_hashing_algorithms_basic_routing(
    algo_class: Type[Union[ConsistentHashing, WeightedConsistentHashing, RendezvousHashing]],
    nodes: List[str],
) -> None:
    """Verify that all hashing algorithms route keys to the available set of nodes."""
    algo = algo_class(nodes)
    node = algo.get_node("test_key")
    assert node in nodes
