from typing import Any

import pytest

from dhash.routing.alternate import ensure_alternate


@pytest.mark.parametrize(
    ("nodes", "ring_map", "primary", "expected_alt"),
    [
        (["n1", "n2"], {10: "n1", 20: "n2"}, "n1", "n2"),
        (["n1"], {10: "n1"}, "n1", "n1"),
    ],
)
def test_ensure_alternate_selects_expected_node(
    nodes: list[str],
    ring_map: dict[int, str],
    primary: str,
    expected_alt: str,
) -> None:
    alt_dict: dict[Any, str] = {}
    ring_keys = sorted(ring_map)

    def dummy_hash(_: Any) -> int:
        return 0

    ensure_alternate("test_key", alt_dict, nodes, ring_keys, ring_map, dummy_hash, primary)

    assert alt_dict["test_key"] == expected_alt


def test_ensure_alternate_keeps_cached_value() -> None:
    alt_dict = {"test_key": "n2"}

    ensure_alternate(
        "test_key",
        alt_dict,
        ["n1", "n2"],
        [10, 20],
        {10: "n1", 20: "n2"},
        lambda _: 0,
        "n1",
    )

    assert alt_dict["test_key"] == "n2"
