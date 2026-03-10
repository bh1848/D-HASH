from unittest.mock import patch

from dhash.routing.router import DHash
from dhash_repro.clients.redis_client import warmup_cluster


class FakePipeline:
    def __init__(self) -> None:
        self.commands: list[tuple[str, str, int] | tuple[str, str]] = []

    def set(self, key: str, payload: bytes, ex: int) -> None:
        self.commands.append(("set", key, ex))

    def get(self, key: str) -> None:
        self.commands.append(("get", key))

    def execute(self) -> None:
        return None


class FakeRedis:
    def __init__(self) -> None:
        self.pipes: list[FakePipeline] = []

    def pipeline(self) -> FakePipeline:
        pipe = FakePipeline()
        self.pipes.append(pipe)
        return pipe


def test_warmup_cluster_defaults_to_up_to_1000_keys() -> None:
    router = DHash(["n1", "n2"], hot_key_threshold=10, window_size=5)
    keys = [f"key-{i}" for i in range(1500)]
    clients = {"n1": FakeRedis(), "n2": FakeRedis()}

    with patch(
        "dhash_repro.clients.redis_client.redis_client_for_node",
        side_effect=lambda node: clients[node],
    ):
        warmup_cluster(router, keys)

    touched = 0
    for client in clients.values():
        for pipe in client.pipes:
            touched += sum(1 for cmd in pipe.commands if cmd[0] == "get")

    assert touched == 1000
