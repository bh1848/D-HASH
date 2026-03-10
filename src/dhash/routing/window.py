def select_window_route(
    cnt: int, threshold: int, window_size: int, primary: str, alternate: str
) -> str:
    delta = max(0, cnt - threshold)
    epoch = (delta - window_size) // window_size
    return alternate if (epoch % 2 == 0) else primary
