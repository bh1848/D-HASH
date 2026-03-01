from dhash.hashing.core import ConsistentHashing, RendezvousHashing, fast_hash64


def test_fast_hash64_deterministic() -> None:
    assert fast_hash64("key1") == fast_hash64("key1")
    assert fast_hash64("key1") != fast_hash64("key2")


def test_consistent_hashing_basic() -> None:
    ch = ConsistentHashing(["node1", "node2", "node3"], replicas=10)
    node = ch.get_node("test_key")
    assert node in ["node1", "node2", "node3"]


def test_rendezvous_hashing() -> None:
    rh = RendezvousHashing(["node1", "node2", "node3"])
    node = rh.get_node("test_key")
    assert node in ["node1", "node2", "node3"]
