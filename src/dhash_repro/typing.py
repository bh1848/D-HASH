from typing import Any, Protocol


class Sharding(Protocol):
    def get_node(self, key: Any, op: str = "read") -> str: ...
