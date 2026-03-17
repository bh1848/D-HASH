from unittest.mock import patch

from dhash_repro.benchmark.collectors import benchmark_cluster


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


class StubSharding:
    def get_node(self, key: object, op: str = "read") -> str:
        return "redis-1"


def test_benchmark_cluster_empty_keys_returns_zero_metrics() -> None:
    fake_redis = FakeRedis()

    with patch(
        "dhash_repro.benchmark.collectors.redis_client_for_node",
        return_value=fake_redis,
    ):
        result = benchmark_cluster([], StubSharding())

    assert result["throughput_ops_s"] == 0.0
    assert result["avg_ms"] == 0.0
    assert result["p95_ms"] == 0.0
    assert result["p99_ms"] == 0.0
    assert fake_redis.pipes == []


def test_benchmark_cluster_node_load_counts_one_write_and_one_read_per_key() -> None:
    fake_redis = FakeRedis()
    keys = ["a", "b", "c", "d"]

    with patch(
        "dhash_repro.benchmark.collectors.redis_client_for_node",
        return_value=fake_redis,
    ):
        result = benchmark_cluster(keys, StubSharding(), pipeline_size=2)

    assert sum(result["node_load"].values()) == 2 * len(keys)

    all_commands = [command for pipe in fake_redis.pipes for command in pipe.commands]
    assert sum(1 for command in all_commands if command[0] == "set") == len(keys)
    assert sum(1 for command in all_commands if command[0] == "get") == len(keys)


def test_benchmark_cluster_returns_expected_result_keys() -> None:
    fake_redis = FakeRedis()

    with patch(
        "dhash_repro.benchmark.collectors.redis_client_for_node",
        return_value=fake_redis,
    ):
        result = benchmark_cluster(["key-1"], StubSharding())

    assert set(result) == {
        "throughput_ops_s",
        "avg_ms",
        "p95_ms",
        "p99_ms",
        "node_load",
    }
