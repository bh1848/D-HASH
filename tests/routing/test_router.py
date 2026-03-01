import pytest
from typing import List
from dhash.routing.router import DHash


@pytest.mark.parametrize(
    "req_count, expect_primary",
    [
        (5, True),
        (10, True),
        (14, True),
        (15, False),
        (20, True),
    ],
)
def test_router_routing_logic_flow(req_count: int, expect_primary: bool) -> None:
    """Verify the high-level routing flow from initial state to windowed alternation."""
    nodes: List[str] = ["n1", "n2"]
    router = DHash(nodes, hot_key_threshold=10, window_size=5)
    key: str = "hot-key"

    current_node: str = ""
    for _ in range(req_count):
        current_node = router.get_node(key, op="read")

    primary: str = router._primary_safe(key)
    if expect_primary:
        assert current_node == primary
    else:
        # After promotion and guard phase, the alternate node must exist in router.alt
        assert current_node == router.alt[key]
        assert current_node != primary
