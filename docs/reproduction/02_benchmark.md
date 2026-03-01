# 02. Benchmark

The benchmark layer executes controlled workloads
against the routing implementation.

Execution entry point:

`dhash-repro`

---

## CLI Interface

```bash
dhash-repro --mode {all|pipeline|zipf|ablation} --alpha 1.5 --repeats 10
```

Parameters:

- `--mode` — experiment configuration
- `--alpha` — workload skew parameter
- `--repeats` — repetition count

---

## Modes

- `all` — run full experiment sequence
- `pipeline` — pipeline-based scenario
- `zipf` — skewed workload scenario
- `ablation` — configuration comparison

Each mode defines a predefined experiment structure.

---

## Workload

Zipf-based workloads simulate skewed key access.

Skew intensity is controlled by `--alpha`.

Workload generation is deterministic
given identical configuration.
