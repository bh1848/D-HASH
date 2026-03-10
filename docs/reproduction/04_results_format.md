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

This file contains the outputs from the synthetic Zipf benchmark.

---

### Threshold Ablation

```text
{dataset}_threshold_ablation.csv
```

This file contains the outputs from D-HASH threshold ablation runs.

---

### Environment Metadata

```text
{dataset}_env_metadata.csv
```

This file stores environment-level metadata collected during the benchmark run.

---

## Interpretation

These files are intended to be compared across:

- routing strategies
- parameter settings
- repeated runs
- datasets

The result format is simple on purpose.
The runner writes flat CSV outputs rather than a larger reporting structure.

---

## Scope

This document describes the current output file names used by the repository.

Column definitions and downstream analysis are implementation details and may be inspected directly from the generated CSV files.
