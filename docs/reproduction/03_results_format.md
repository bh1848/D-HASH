# 03 Results Format

Each benchmark run produces:

- JSON (full metadata and per-run details)
- CSV (aggregated summary across repeats)

---

## CSV Columns

The CSV file contains one row per:

- algorithm
- workload configuration
- pipeline size

### Workload Metadata

- run_id
- kind
- name
- alpha
- num_ops
- num_keys
- read_ratio
- pipeline
- seed
- threshold
- window
- nodes
- repeats

### Latency Metrics (ns)

- avg_latency_ns_mean
- p50_latency_ns_mean
- p95_latency_ns_mean
- p99_latency_ns_mean

These values are computed from weighted percentiles.
Weights correspond to the number of operations per pipeline batch.

### Load Distribution Metrics

- load_mean_mean
- load_stddev_mean
- load_max_mean
- load_min_mean

Load is measured as the number of operations routed to each physical node.

For `num_ops = 200000` and `nodes = 5`,
`load_mean_mean` equals `40000`.

---

## Interpretation Notes

### 1. Latency Scope

Latency values reflect routing-layer execution under pipelined execution.

They primarily capture:

- Routing decision cost
- Python execution overhead
- Batch-level measurement aggregation

They do not represent full network-level or cross-service latency unless Redis I/O is explicitly included in the measurement configuration.

---

### 2. Weighted Percentile

In pipelined workloads, a single latency sample may represent multiple operations.

Percentile calculation uses:

```python
def _weighted_percentile(samples, q):
    samples_sorted = sorted(samples, key=lambda x: x[0])
    total_w = sum(w for _, w in samples_sorted)
    target = q * total_w
```

Each sample is weighted by the number of operations in that batch.

This preserves operation-level interpretation rather than batch-level interpretation.

---

### 3. Load Imbalance Metric

`load_stddev_mean` represents the standard deviation of request counts across physical nodes.

Lower values indicate a more even distribution of routed operations.

The metric does not imply system-wide performance improvement.
It reflects distribution characteristics under the evaluated workload.

---

### 4. Pipeline Parameter

The `pipeline` parameter changes batch size but does not alter routing semantics.

Load distribution metrics are expected to remain identical across pipeline values,
while latency metrics may vary due to batching effects.

---

### 5. Weighted CH (WCH)

When all node weights are identical, Weighted Consistent Hashing produces the same distribution as standard Consistent Hashing.

Differences appear only when heterogeneous node weights are applied.

---

## Reproducibility

To regenerate results:

```bash
python -m benchmarks.runner --algo all --repeats 3
```
