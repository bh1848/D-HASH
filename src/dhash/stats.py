from typing import List, Tuple


def weighted_percentile(samples: List[Tuple[float, int]], q: float) -> float:
    if not samples:
        return 0.0

    samples_sorted = sorted(samples, key=lambda x: x[0])
    total_w = sum(w for _, w in samples_sorted)

    if total_w <= 0:
        return 0.0

    target = q * total_w
    cum = 0.0
    prev_v = samples_sorted[0][0]

    for v, w in samples_sorted:
        next_cum = cum + w
        if next_cum >= target:
            if w == 0:
                return v
            frac = (target - cum) / w
            return prev_v + (v - prev_v) * frac
        prev_v = v
        cum = next_cum

    return samples_sorted[-1][0]
