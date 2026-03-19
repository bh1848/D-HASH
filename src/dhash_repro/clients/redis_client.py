import logging
import random
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from typing import TYPE_CHECKING, Any, Dict, Iterable, List, Optional, cast

from redis import ConnectionPool, Redis

from dhash.routing.alternate import ensure_alternate

from ..config.defaults import REDIS_PORT, SEED, TTL_SECONDS
from ..typing import Sharding

logger = logging.getLogger(__name__)
_connection_pools: Dict[str, ConnectionPool] = {}


if TYPE_CHECKING:
    RedisInstance = Any
else:
    RedisInstance = Redis


def _redis_client(host: str) -> RedisInstance:
    if host not in _connection_pools:
        _connection_pools[host] = ConnectionPool(host=host, port=REDIS_PORT, db=0)
    return Redis(connection_pool=_connection_pools[host])


def redis_client_for_node(node: str) -> RedisInstance:
    return _redis_client(node)


def _unique_keys(keys: Iterable[Any]) -> List[Any]:
    return list(dict.fromkeys(keys))


def _maybe_add_alternate_write(
    sharding: Sharding,
    key: Any,
    primary_node: str,
    write_buckets: Dict[str, List[Any]],
) -> None:
    if not hasattr(sharding, "alt") or not hasattr(sharding, "ch"):
        return

    rich_sharding = cast(Any, sharding)
    ensure_alternate(
        key,
        rich_sharding.alt,
        rich_sharding.nodes,
        getattr(rich_sharding.ch, "sorted_keys", []),
        getattr(rich_sharding.ch, "ring", {}),
        getattr(rich_sharding, "_h", hash),
        primary_node,
    )
    a_node = cast(Dict[Any, str], rich_sharding.alt).get(key)
    if a_node and a_node != primary_node:
        write_buckets[a_node].append(key)


def _build_write_buckets(
    sharding: Sharding,
    keys: Iterable[Any],
    *,
    include_alternate: bool,
) -> Dict[str, List[Any]]:
    write_buckets: Dict[str, List[Any]] = defaultdict(list)

    for key in keys:
        primary_node = sharding.get_node(key, op="write")
        write_buckets[primary_node].append(key)
        if include_alternate:
            _maybe_add_alternate_write(sharding, key, primary_node, write_buckets)

    return write_buckets


def _execute_write_buckets(
    write_buckets: Dict[str, List[Any]],
    *,
    payload: bytes,
    ttl_seconds: int,
    log_prefix: str,
) -> None:
    for node, node_keys in write_buckets.items():
        try:
            cli = redis_client_for_node(node)
            pipe = cli.pipeline()
            for key in node_keys:
                pipe.set(str(key), payload, ex=ttl_seconds)
            pipe.execute()
        except Exception as e:
            logger.warning("%s write failed on %s: %s", log_prefix, node, e)


def _execute_read_buckets(read_buckets: Dict[str, List[Any]], log_prefix: str) -> None:
    for node, node_keys in read_buckets.items():
        try:
            cli = redis_client_for_node(node)
            pipe = cli.pipeline()
            for key in node_keys:
                pipe.get(str(key))
            pipe.execute()
        except Exception as e:
            logger.warning("%s read failed on %s: %s", log_prefix, node, e)


def preload_cluster(sharding: Sharding, keys: List[Any], ttl_seconds: int = TTL_SECONDS) -> None:
    unique_keys = _unique_keys(keys)
    write_buckets = _build_write_buckets(sharding, unique_keys, include_alternate=True)

    _execute_write_buckets(
        write_buckets,
        payload=b'{"preload":1}',
        ttl_seconds=ttl_seconds,
        log_prefix="Preload",
    )

    logger.info(
        "[Preload] Populated %d unique keys across %d nodes.", len(unique_keys), len(write_buckets)
    )


def warmup_cluster(
    sharding: Sharding,
    keys: List[Any],
    *,
    sample_size: int = 1000,
    ratio: Optional[float] = None,
    cap: Optional[int] = None,
) -> None:
    if not keys:
        logger.info("[Warmup] Skipped because there are no keys.")
        return

    if ratio is None:
        n = min(len(keys), max(1, int(sample_size)))
    else:
        effective_cap = sample_size if cap is None else cap
        n = max(1, min(int(len(keys) * ratio), int(effective_cap)))

    rng = random.Random(SEED)
    sample = rng.sample(keys, n) if len(keys) >= n else list(keys)

    write_buckets = _build_write_buckets(sharding, sample, include_alternate=True)
    read_buckets: Dict[str, List[Any]] = defaultdict(list)

    for key in sample:
        read_buckets[sharding.get_node(key, op="read")].append(key)

    _execute_write_buckets(
        write_buckets,
        payload=b'{"warm":1}',
        ttl_seconds=60,
        log_prefix="Warmup",
    )
    _execute_read_buckets(read_buckets, "Warmup")

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
