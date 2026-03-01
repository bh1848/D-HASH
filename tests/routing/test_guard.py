from dhash.routing.guard import check_guard_phase


def test_check_guard_phase() -> None:
    assert check_guard_phase(49, threshold=50, window_size=10) is True
    assert check_guard_phase(50, threshold=50, window_size=10) is True
    assert check_guard_phase(59, threshold=50, window_size=10) is True

    assert check_guard_phase(60, threshold=50, window_size=10) is False
