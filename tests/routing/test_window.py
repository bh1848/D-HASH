import pytest
from dhash.routing.window import select_window_route


@pytest.mark.parametrize(
    "cnt, threshold, window, expected_node",
    [
        (60, 50, 10, "A"),
        (69, 50, 10, "A"),
        (70, 50, 10, "P"),
        (79, 50, 10, "P"),
        (80, 50, 10, "A"),
    ],
)
def test_select_window_route_oscillation(
    cnt: int, threshold: int, window: int, expected_node: str
) -> None:
    """Verify that routing oscillates between Primary and Alternate every W requests."""
    assert select_window_route(cnt, threshold, window, "P", "A") == expected_node
