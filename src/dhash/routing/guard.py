def check_guard_phase(cnt: int, threshold: int, window_size: int) -> bool:
    """
    Returns True if the routing should stick to the primary node
    to allow the alternate node's cache to warm up.
    """
    delta = max(0, cnt - threshold)
    return delta < window_size
