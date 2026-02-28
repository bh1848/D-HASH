# Benchmarks

This directory provides reproducible client-side routing benchmarks for D-HASH and baseline algorithms.

The benchmark focuses on:

- Zipf-based key distributions
- Read/Write ratio control
- Pipeline-aware weighted percentile measurement
- Load imbalance statistics
- Multi-algorithm comparison (CH / WCH / HRW / D-HASH)

---

## Algorithms

The following routing algorithms can be benchmarked:

- `ch`     : Consistent Hashing
- `wch`    : Weighted Consistent Hashing
- `hrw`    : Rendezvous Hashing
- `dhash`  : Dynamic Hot-key Aware Scalable Hashing
- `all`    : Run all of the above

---

## Run

Basic run (all algorithms):

```bash
python -m benchmarks.runner --out benchmarks/outputs
```

Run only D-HASH:

```bash
python -m benchmarks.runner --algo dhash --out benchmarks/outputs
```

Run selected algorithms:

```bash
python -m benchmarks.runner --algo ch,hrw --out benchmarks/outputs
```

Custom workload parameters:

```bash
python -m benchmarks.runner \
  --nodes 5 \
  --threshold 50 \
  --window 500 \
  --replicas 100 \
  --num-ops 200000 \
  --num-keys 10000 \
  --alphas 1.1,1.3,1.5 \
  --read-ratio 0.95 \
  --pipelines 50,100,200,500 \
  --repeats 3 \
  --out benchmarks/outputs
```

---

## Measurement Model

Latency measurement:

- Each pipeline batch is timed using `perf_counter_ns`
- Per-op latency is computed as:
  
  batch_latency_ns / batch_size

- Weighted percentile (P50 / P95 / P99) is computed using:

  value = batch_avg_latency  
  weight = batch_size

This ensures statistical consistency when pipeline sizes differ.

---

## Load Metrics

For each workload and algorithm:

- `load_mean`
- `load_max`
- `load_min`
- `load_stddev`

These are computed from per-node request counts.

Note:
Pipeline size affects latency aggregation,
but does not affect node load distribution.

---

## Output

Each run produces:

```text
benchmarks/outputs/
  ├── <run_id>.json
  └── <run_id>.csv
```

### JSON

Contains:

- Full run configuration
- All workload summaries
- Per-repeat detailed results
- Per-node load breakdown

### CSV

Flattened summary table including:

- run_id
- algo
- workload parameters
- avg_latency_ns_mean
- p50_latency_ns_mean
- p95_latency_ns_mean
- p99_latency_ns_mean
- load_stddev_mean
- load_mean_mean
- load_max_mean
- load_min_mean

The CSV file is suitable for plotting or statistical comparison.

---

## Reproducibility

All workloads are deterministic with respect to:

- seed
- alpha
- num_keys
- num_ops

Repeat runs use `seed + repeat_index` to avoid identical key streams.

---

## Recommended Workflow

```bash
# install editable package
python -m pip install -e ".[dev]"

# run benchmarks
python -m benchmarks.runner --out benchmarks/outputs

# inspect results
ls benchmarks/outputs
```