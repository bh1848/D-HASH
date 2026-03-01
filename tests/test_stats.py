import pytest
from typing import List, Tuple
from dhash.stats import weighted_percentile


@pytest.mark.parametrize(
    "samples, q, expected",
    [
        ([], 0.95, 0.0),
        ([(10.0, 0), (20.0, 0)], 0.5, 0.0),
        ([(50.0, 100)], 0.99, 50.0),
        ([(10.0, 10), (20.0, 10)], 0.5, 10.0),
        ([(10.0, 10), (20.0, 10)], 0.75, 15.0),
    ],
)
def test_weighted_percentile_robustness(
    samples: List[Tuple[float, int]], q: float, expected: float
) -> None:
    """Verify weighted percentile calculation accuracy and robustness."""
    assert weighted_percentile(samples, q) == pytest.approx(expected)
