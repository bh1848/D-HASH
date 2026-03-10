# Datasets

## Overview

This document describes the datasets used by the D-HASH experiment runner.

The current implementation supports two dataset names:

- `nasa`
- `ebay`

These datasets are used to build request traces for benchmark execution.

---

## NASA

The NASA dataset is used as an HTTP-style request trace.

The runner can load:

- a processed trace file
- a raw log file
- a raw zip file

If a processed file is available, the runner uses it directly.
If not, it can preprocess a raw file and generate a processed trace.

---

## eBay

The eBay dataset is used as a second real-world style workload.

The runner can load:

- a processed trace file
- a raw csv file
- a raw zip file

As with NASA, the runner prefers a processed file when one already exists.

---

## Processed Trace

A processed trace is the format expected by the benchmark runner during normal execution.

Using a processed trace avoids repeating raw-data preprocessing on every run.

---

## Raw Dataset

A raw dataset is the original input file used to build a processed trace.

The repository supports raw loading mainly for reproduction convenience.

---

## Selection

The active dataset is chosen through:

```text
DHASH_DATASET
```

Supported values are:

- `nasa`
- `ebay`

The runner then resolves the corresponding processed or raw path from the configured environment variables or default data directories.

---

## Scope

This document describes dataset usage at the level needed to run experiments.

It does not document the original external sources of the raw datasets or their licenses.
