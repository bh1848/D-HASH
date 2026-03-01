import pytest
from typing import Dict, List, Any
from dhash.routing.alternate import ensure_alternate


@pytest.mark.parametrize(
    "nodes, ring_map, primary, expected_alt",
    [
        (["n1", "n2"], {10: "n1", 20: "n2"}, "n1", "n2"),
        (["n1"], {10: "n1"}, "n1", "n1"),
    ],
)
def test_ensure_alternate_logic(
    nodes: List[str], ring_map: Dict[int, str], primary: str, expected_alt: str
) -> None:
    """Verify alternate selection logic across various configurations."""
    alt_dict: Dict[Any, str] = {}
    ring_keys = sorted(ring_map.keys())

    def dummy_hash(x: Any) -> int:
        return 0

    ensure_alternate("test_key", alt_dict, nodes, ring_keys, ring_map, dummy_hash, primary)
    assert alt_dict["test_key"] == expected_alt
