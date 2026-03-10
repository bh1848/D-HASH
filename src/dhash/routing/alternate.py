from bisect import bisect
from typing import Any, Callable, Dict, List


def ensure_alternate(
    key: Any,
    alt_dict: Dict[Any, str],
    nodes: List[str],
    ring_keys: List[int],
    ring_map: Dict[int, str],
    hash_fn: Callable[[Any], int],
    primary: str,
) -> None:
    if key in alt_dict:
        return

    if not ring_keys or not ring_map or len(nodes) <= 1:
        alt_dict[key] = primary
        return

    hk = hash_fn(key)
    i = bisect(ring_keys, hk) % len(ring_keys)
    stride = 1 + (hash_fn(f"{key}|alt") % (len(nodes) - 1))

    seen = set()
    ordered = []
    j = i

    for _ in range(len(ring_keys)):
        j = (j + 1) % len(ring_keys)
        cand = ring_map[ring_keys[j]]
        if cand == primary or cand in seen:
            continue
        seen.add(cand)
        ordered.append(cand)
        if len(ordered) == len(nodes) - 1:
            break

    alt_dict[key] = ordered[stride - 1] if len(ordered) >= stride else primary
