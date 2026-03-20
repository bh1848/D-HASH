from typing import cast

from dhash.routing.guard import check_guard_phase
from dhash.routing.window import select_window_route


def route_naive(cnt: int, threshold: int, primary: str, alternate: str) -> str:
    if cnt < threshold:
        return primary
    return alternate if (cnt % 2 == 0) else primary


def classify_range(cnt: int, threshold: int, window_size: int) -> str:
    delta = max(0, cnt - threshold)
    if cnt < threshold:
        return "threshold 미만"
    if check_guard_phase(cnt, threshold, window_size):
        return "guard phase"
    epoch = (delta - window_size) // window_size
    return f"epoch {epoch}"


def route_current(cnt: int, threshold: int, window_size: int, primary: str, alternate: str) -> str:
    if cnt < threshold:
        return primary
    if check_guard_phase(cnt, threshold, window_size):
        return primary
    return cast(str, select_window_route(cnt, threshold, window_size, primary, alternate))


def main() -> None:
    threshold = 10
    window_size = 5
    primary = "p(k)"
    alternate = "a(k)"

    header = "| cnt | δ(k) | 구간 | 초기 구조 | 현재 구조 |"
    divider = "|---:|---:|---|---|---|"

    print(header)
    print(divider)

    for cnt in range(1, 36):
        delta = max(0, cnt - threshold)
        naive = route_naive(cnt, threshold, primary, alternate)
        current = route_current(cnt, threshold, window_size, primary, alternate)
        marker = " <- 차이" if naive != current else ""
        print(
            f"| {cnt} | {delta} | {classify_range(cnt, threshold, window_size)} | "
            f"{naive} | {current} |{marker}"
        )


if __name__ == "__main__":
    main()
