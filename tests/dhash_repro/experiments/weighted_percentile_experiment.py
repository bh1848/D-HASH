from __future__ import annotations

from typing import cast

import numpy as np

from dhash import weighted_percentile

Sample = tuple[float, int]


class SyntheticPercentileExperiment:
    def __init__(self, seed: int = 42) -> None:
        self.rng = np.random.default_rng(seed)

    def run(self) -> None:
        samples_1a = self._make_samples(n=200, ops=50, mean_log=-6.5, sigma_log=0.4)
        self._run_scenario(
            title="Scenario 1a: Homogeneous small batches (ops=50, N=200)",
            samples=samples_1a,
            explanation="Same result: all samples have equal weight (ops=50 each)",
        )

        samples_1b = self._make_samples(n=100, ops=1000, mean_log=-6.5, sigma_log=0.4)
        self._run_scenario(
            title="Scenario 1b: Homogeneous large batches (ops=1000, N=10)",
            samples=samples_1b,
            explanation="Same result: all samples have equal weight (ops=1000 each)",
        )

        node_a_2 = self._make_samples(n=200, ops=50, mean_log=-6.5, sigma_log=0.4)
        node_b_2 = self._make_samples(n=10, ops=1000, mean_log=-7.5, sigma_log=0.2)
        samples_2 = node_a_2 + node_b_2
        ops_a_2 = 200 * 50
        ops_b_2 = 10 * 1000
        self._run_scenario(
            title="Scenario 2: Mixed batches (Node A: ops=50 ×200, Node B: ops=1000 ×10)",
            samples=samples_2,
            node_info=f"Total ops: Node A={ops_a_2}, Node B={ops_b_2} (evenly split)",
            explanation=(
                "numpy overestimates: Node A has 200 samples vs Node B's 10, "
                "despite equal total ops"
            ),
        )

        node_a_3 = self._make_samples(n=50, ops=10, mean_log=-5.5, sigma_log=0.4)
        node_b_3 = self._make_samples(n=5, ops=1000, mean_log=-7.5, sigma_log=0.15)
        samples_3 = node_a_3 + node_b_3
        ops_a_3 = 50 * 10
        ops_b_3 = 5 * 1000
        self._run_scenario(
            title="Scenario 3: Extreme skew (Node A: ops=10 ×50, Node B: ops=1000 ×5)",
            samples=samples_3,
            node_info=f"Total ops: Node A={ops_a_3}, Node B={ops_b_3} (Node B holds 91% of ops)",
            explanation=(
                "numpy overestimates by ~2x on P95: 50 Node A samples dominate numpy, "
                "but Node B holds most of total ops"
            ),
        )

    def _make_samples(
        self,
        n: int,
        ops: int,
        mean_log: float,
        sigma_log: float,
    ) -> list[Sample]:
        log_values = self.rng.normal(loc=mean_log, scale=sigma_log, size=n)
        latencies = np.exp(log_values)
        return [(float(lat), ops) for lat in latencies]

    def _run_scenario(
        self,
        title: str,
        samples: list[Sample],
        explanation: str,
        node_info: str | None = None,
    ) -> None:
        np95 = self._unweighted_percentile(samples, 0.95) * 1000.0
        np99 = self._unweighted_percentile(samples, 0.99) * 1000.0
        wp95 = weighted_percentile(samples, 0.95) * 1000.0
        wp99 = weighted_percentile(samples, 0.99) * 1000.0
        diff_p95 = (np95 - wp95) / wp95 * 100.0 if wp95 > 0 else 0.0
        diff_p99 = (np99 - wp99) / wp99 * 100.0 if wp99 > 0 else 0.0

        print(f"\n=== {title} ===")
        if node_info:
            print(node_info)
        print(f"numpy    P95={np95:.3f}ms  P99={np99:.3f}ms")
        print(f"weighted P95={wp95:.3f}ms  P99={wp99:.3f}ms")
        print(f"diff     P95={diff_p95:+.1f}%   P99={diff_p99:+.1f}%")
        print(f"→ {explanation}")

    @staticmethod
    def _unweighted_percentile(samples: list[Sample], q: float) -> float:
        values = [value for value, _ in samples]
        percentile = np.percentile(values, q * 100.0)
        return float(cast(float, percentile))


if __name__ == "__main__":
    SyntheticPercentileExperiment().run()
