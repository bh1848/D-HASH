import pytest
from dhash.routing.guard import check_guard_phase


@pytest.mark.parametrize(
    "cnt, threshold, window, expected",
    [
        (49, 50, 10, True),
        (50, 50, 10, True),
        (59, 50, 10, True),
        (60, 50, 10, False),
        (100, 50, 10, False),
    ],
)
def test_check_guard_phase_boundaries(
    cnt: int, threshold: int, window: int, expected: bool
) -> None:
    """Verify that the guard phase correctly delays routing transitions."""
    assert check_guard_phase(cnt, threshold, window) is expected
