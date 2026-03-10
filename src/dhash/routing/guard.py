def check_guard_phase(cnt: int, threshold: int, window_size: int) -> bool:
    delta = max(0, cnt - threshold)
    return delta < window_size
