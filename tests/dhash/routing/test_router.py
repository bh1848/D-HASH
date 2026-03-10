import pytest

from dhash.config import DEFAULT_HOT_KEY_THRESHOLD, DEFAULT_WINDOW_SIZE
from dhash.hashing.core import ConsistentHashing
from dhash.routing.router import DHash


@pytest.mark.parametrize(
    ("req_count", "expect_primary"),
    [
        (5, True),
        (10, True),
        (14, True),
        (15, False),
        (20, True),
    ],
)
def test_router_routing_logic_flow(req_count: int, expect_primary: bool) -> None:
    router = DHash(["n1", "n2"], hot_key_threshold=10, window_size=5)
    key = "hot-key"

    current_node = ""
    for _ in range(req_count):
        current_node = router.get_node(key, op="read")

    primary = router._primary_safe(key)
    if expect_primary:
        assert current_node == primary
    else:
        assert current_node == router.alt[key]
        assert current_node != primary


def test_router_uses_paper_aligned_defaults() -> None:
    router = DHash(["n1", "n2"])

    assert router.T == DEFAULT_HOT_KEY_THRESHOLD
    assert router.W == DEFAULT_WINDOW_SIZE


def test_write_requests_always_use_primary() -> None:
    router = DHash(["n1", "n2"], hot_key_threshold=1, window_size=3)
    key = "write-key"

    first = router.get_node(key, op="write")
    second = router.get_node(key, op="write")

    assert first == router._primary_safe(key)
    assert second == router._primary_safe(key)
    assert key not in router.reads


def test_membership_change_invalidates_alternate_cache_automatically() -> None:
    ring = ConsistentHashing(["n1", "n2"], replicas=10)
    router = DHash(["n1", "n2"], hot_key_threshold=1, window_size=3, ring=ring)
    key = "hot-key"

    router.get_node(key, op="read")
    assert key in router.alt

    ring.add_node("n3")

    router.get_node(key, op="read")

    assert key in router.alt
    assert set(router.nodes) == {"n1", "n2", "n3"}
    assert router.alt[key] in {"n1", "n2", "n3"}
