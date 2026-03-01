import logging
import random
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List
from redis import Redis, ConnectionPool
from ..config.defaults import SEED

logger = logging.getLogger(__name__)
_connection_pools: Dict[str, ConnectionPool] = {}


def _redis_client(host: str) -> Redis[Any]:
    if host not in _connection_pools:
        _connection_pools[host] = ConnectionPool(host=host, port=6379, db=0)
    return Redis(connection_pool=_connection_pools[host])


def redis_client_for_node(node: str) -> Redis[Any]:
    return _redis_client(node)


def warmup_cluster(sharding: Any, keys: List[Any], ratio: float = 0.01, cap: int = 1000) -> None:
    n = max(1, min(int(len(keys) * ratio), cap))
    rng = random.Random(SEED)
    sample = rng.sample(keys, n) if len(keys) >= n else list(keys)

    write_buckets: Dict[str, List[Any]] = defaultdict(list)
    read_buckets: Dict[str, List[Any]] = defaultdict(list)

    for k in sample:
        p_node = sharding.get_node(k, op="write")
        write_buckets[p_node].append(k)
        # Alternate node warm-up if supported
        if hasattr(sharding, "alt") and hasattr(sharding, "_h"):
            try:
                # Force evaluate alternate to populate sharding.alt dict
                sharding.get_node(k, op="read")
            except Exception:
                pass
            a_node = sharding.alt.get(k)
            if a_node and a_node != p_node:
                write_buckets[a_node].append(k)
        read_buckets[sharding.get_node(k, op="read")].append(k)

    payload = b'{"warm":1}'
    for node, node_keys in write_buckets.items():
        try:
            cli = redis_client_for_node(node)
            pipe = cli.pipeline()
            for k in node_keys:
                pipe.set(str(k), payload, ex=60)
            pipe.execute()
        except Exception as e:
            logger.warning(f"Warmup write failed on {node}: {e}")

    for node, node_keys in read_buckets.items():
        try:
            cli = redis_client_for_node(node)
            pipe = cli.pipeline()
            for k in node_keys:
                pipe.get(str(k))
            pipe.execute()
        except Exception as e:
            logger.warning(f"Warmup read failed on {node}: {e}")

    logger.info(
        "[Warmup] Populated %d keys across %d nodes.",
        n,
        len(set(write_buckets) | set(read_buckets)),
    )


def flush_databases(redis_nodes: List[str], flush_async: bool = False) -> None:
    def _init_one(container: str) -> None:
        try:
            cli = _redis_client(container)
            if flush_async:
                try:
                    cli.flushdb(asynchronous=True)
                except TypeError:
                    cli.execute_command("FLUSHDB", "ASYNC")
                for _ in range(10_000):
                    try:
                        if int(cli.dbsize()) == 0:
                            break
                    except Exception:
                        pass
                    time.sleep(0.005)
            else:
                try:
                    cli.flushdb()
                except TypeError:
                    cli.execute_command("FLUSHDB")
        except Exception as e:
            logger.warning("Redis(%s) flush failed: %s", container, e)

    with ThreadPoolExecutor(max_workers=len(redis_nodes)) as ex:
        list(ex.map(_init_one, redis_nodes))
