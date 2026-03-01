from dhash.routing.window import select_window_route


def test_select_window_route() -> None:
    assert select_window_route(60, 50, 10, primary="P", alternate="A") == "A"

    assert select_window_route(70, 50, 10, primary="P", alternate="A") == "P"

    assert select_window_route(80, 50, 10, primary="P", alternate="A") == "A"
