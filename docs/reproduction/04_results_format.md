# Results Format

## Overview

This document describes the result files written by the current experiment runner.

The repository writes CSV outputs for each experiment stage.

---

## Result Files

The current implementation writes the following files.

### Pipeline Sweep

```text
{dataset}_pipeline_sweep.csv
```

This file contains the outputs from pipeline-mode runs for the selected dataset.

---

### Zipf Results

```text
{dataset}_zipf_results.csv
```

This file contains the outputs from the Zipf benchmark run on dataset-derived key bases.

---

### Threshold Ablation

```text
{dataset}_threshold_ablation.csv
```

This file contains the outputs from D-HASH threshold ablation runs.

---

### Microbench

```text
{dataset}_microbench_ns.csv
```

This file contains routing-only microbenchmark results in `ns/op`.

---

### Redistribution

```text
{dataset}_redistribution.csv
```

This file contains offline move-rate results for membership changes.

---

### Stage Environment Metadata

```text
{dataset}_pipeline_env_meta.csv
{dataset}_microbench_env_meta.csv
{dataset}_zipf_env_meta.csv
{dataset}_ablation_env_meta.csv
{dataset}_redistribution_env_meta.csv
```

These files store stage-specific environment and parameter metadata.

They are most useful when you want to understand the exact configuration used by one stage, such as:

- the Zipf stage pipeline and threshold
- the microbench operation count
- the redistribution sample size

---

### Environment Metadata

```text
{dataset}_env_metadata.csv
```

This file stores environment-level metadata collected during the benchmark run.

This file is especially useful when multiple stages are executed together with `DHASH_MODE=all`, because it acts as a shared run-level metadata record for the whole result set.

When only one stage is executed, this file may overlap with the corresponding stage-specific env metadata.

---

## Interpretation

These files are intended to be compared across:

- routing strategies
- parameter settings
- repeated runs
- datasets

The result format is simple on purpose.
The runner writes flat CSV outputs under the `persistence/` directory rather than a larger reporting structure.

---

## Scope

This document describes the current output file names used by the repository.

Column definitions and downstream analysis are implementation details and may be inspected directly from the generated CSV files.
