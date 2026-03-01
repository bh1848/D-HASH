from dhash.routing.alternate import ensure_alternate


def test_ensure_alternate_skips_if_exists() -> None:
    alt_dict = {"key1": "node2"}
    ensure_alternate("key1", alt_dict, ["node1", "node2"], [], {}, lambda x: 0, "node1")
    assert alt_dict["key1"] == "node2"


def test_ensure_alternate_picks_different_node() -> None:
    alt_dict: dict[str, str] = {}
    nodes = ["n1", "n2", "n3"]
    ring_keys = [10, 20, 30]
    ring_map = {10: "n1", 20: "n2", 30: "n3"}

    ensure_alternate("key1", alt_dict, nodes, ring_keys, ring_map, lambda x: 10, "n1")

    assert "key1" in alt_dict
    assert alt_dict["key1"] != "n1"
    assert alt_dict["key1"] in nodes
