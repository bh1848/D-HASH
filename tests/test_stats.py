from dhash.stats import weighted_percentile


def test_weighted_percentile_empty() -> None:
    assert weighted_percentile([], 0.95) == 0.0


def test_weighted_percentile_calculates_correctly() -> None:
    samples = [
        (10.0, 90),
        (100.0, 10),
    ]

    assert weighted_percentile(samples, 0.50) == 10.0

    p95 = weighted_percentile(samples, 0.95)
    assert p95 > 10.0 and p95 <= 100.0
