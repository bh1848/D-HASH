import logging
import random
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from typing import TYPE_CHECKING, Any, Dict, Iterable, List, Optional, cast

from redis import ConnectionPool, Redis

from dhash.routing.alternate import ensure_alternate

from ..config.defaults import SEED, TTL_SECONDS

logger = logging.getLogger(__name__)
_connection_pools: Dict[str, ConnectionPool] = {}


if TYPE_CHECKING:
    RedisInstance = Any
else:
    RedisInstance = Redis


def _redis_client(host: str) -> RedisInstance:
    if host not in _connection_pools:
        _connection_pools[host] = ConnectionPool(host=host, port=6379, db=0)
    return Redis(connection_pool=_connection_pools[host])


def redis_client_for_node(node: str) -> RedisInstance:
    return _redis_client(node)


def _unique_keys(keys: Iterable[Any]) -> List[Any]:
    return list(dict.fromkeys(keys))


def preload_cluster(sharding: Any, keys: List[Any], ttl_seconds: int = TTL_SECONDS) -> None:
    unique_keys = _unique_keys(keys)
    write_buckets: Dict[str, List[Any]] = defaultdict(list)

    for k in unique_keys:
        p_node = sharding.get_node(k, op="write")
        write_buckets[p_node].append(k)

        if hasattr(sharding, "alt") and hasattr(sharding, "ch"):
            ensure_alternate(
                k,
                sharding.alt,
                sharding.nodes,
                getattr(sharding.ch, "sorted_keys", []),
                getattr(sharding.ch, "ring", {}),
                getattr(sharding, "_h", hash),
                p_node,
            )
            a_node = cast(Dict[Any, str], sharding.alt).get(k)
            if a_node and a_node != p_node:
                write_buckets[a_node].append(k)

    payload = b'{"preload":1}'
    for node, node_keys in write_buckets.items():
        try:
            cli = redis_client_for_node(node)
            pipe = cli.pipeline()
            for k in node_keys:
                pipe.set(str(k), payload, ex=ttl_seconds)
            pipe.execute()
        except Exception as e:
            logger.warning("Preload write failed on %s: %s", node, e)

    logger.info(
        "[Preload] Populated %d unique keys across %d nodes.", len(unique_keys), len(write_buckets)
    )


def warmup_cluster(
    sharding: Any,
    keys: List[Any],
    *,
    sample_size: int = 1000,
    ratio: Optional[float] = None,
    cap: Optional[int] = None,
) -> None:
    unique_keys = _unique_keys(keys)
    if not unique_keys:
        logger.info("[Warmup] Skipped because there are no keys.")
        return

    if ratio is None:
        n = min(len(unique_keys), max(1, int(sample_size)))
    else:
        effective_cap = sample_size if cap is None else cap
        n = max(1, min(int(len(unique_keys) * ratio), int(effective_cap)))

    rng = random.Random(SEED)
    sample = rng.sample(unique_keys, n) if len(unique_keys) > n else list(unique_keys)

    write_buckets: Dict[str, List[Any]] = defaultdict(list)
    read_buckets: Dict[str, List[Any]] = defaultdict(list)

    for k in sample:
        p_node = sharding.get_node(k, op="write")
        write_buckets[p_node].append(k)

        if hasattr(sharding, "alt") and hasattr(sharding, "ch"):
            ensure_alternate(
                k,
                sharding.alt,
                sharding.nodes,
                getattr(sharding.ch, "sorted_keys", []),
                getattr(sharding.ch, "ring", {}),
                getattr(sharding, "_h", hash),
                p_node,
            )
            a_node = cast(Dict[Any, str], sharding.alt).get(k)
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
            logger.warning("Warmup write failed on %s: %s", node, e)

    for node, node_keys in read_buckets.items():
        try:
            cli = redis_client_for_node(node)
            pipe = cli.pipeline()
            for k in node_keys:
                pipe.get(str(k))
            pipe.execute()
        except Exception as e:
            logger.warning("Warmup read failed on %s: %s", node, e)

    logger.info(
        "[Warmup] Touched %d sampled keys across %d nodes.",
        len(sample),
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
                    cast(Any, cli).execute_command("FLUSHDB", "ASYNC")

                for _ in range(10_000):
                    try:
                        db_size = cli.dbsize()
                        if int(cast(Any, db_size)) == 0:
                            break
                    except Exception:
                        pass
                    time.sleep(0.005)
            else:
                try:
                    cli.flushdb()
                except TypeError:
                    cast(Any, cli).execute_command("FLUSHDB")
        except Exception as e:
            logger.warning("Redis(%s) flush failed: %s", container, e)

    with ThreadPoolExecutor(max_workers=len(redis_nodes)) as ex:
        list(ex.map(_init_one, redis_nodes))
