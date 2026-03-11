# Datasets

## Overview

This document describes the datasets supported by the D-HASH experiment runner.

The current implementation supports the following dataset names:

- `nasa`
- `ebay`

These datasets are used to build request traces for benchmark execution.

---

## Dataset Sources

### 1. NASA HTTP Web Server Log
- Source: https://www.kaggle.com/datasets/adchatakora/nasa-http-access-logs

### 2. eBay Auction Dataset
- Source: https://www.kaggle.com/datasets/onlineauctions/online-auctions-dataset

> Raw dataset files are **not included** in this repository.
> Please download them directly from the original source pages and review the applicable terms or license information before use.

---

## NASA

The NASA dataset is used as an HTTP-style request trace.

The runner can load:

- a processed trace file
- a raw log file
- a raw zip file

If a processed file is available, the runner uses it directly.
Otherwise, it can preprocess a raw file and generate a processed trace.

---

## eBay

The eBay dataset is used as a second real-world style workload.

The runner can load:

- a processed trace file
- a raw CSV file
- a raw zip file

As with NASA, the runner prefers a processed file when one already exists.

---

## Processed Trace

A processed trace is the format expected by the benchmark runner during normal execution.

Using a processed trace avoids repeating raw-data preprocessing on every run and helps keep experiment execution consistent.

---

## Raw Dataset

A raw dataset is the original input file used to generate a processed trace.

Raw loading is supported mainly for reproduction convenience.

---

## Dataset Selection

The active dataset is selected through the following environment variable:

```text
DHASH_DATASET
```

Supported values are:

- `nasa`
- `ebay`

The runner resolves the corresponding processed or raw path from the configured environment variables or the default data directories.

---

## Scope

- Processed traces are recommended for regular benchmark execution.
- Raw datasets are intended for preprocessing and reproduction workflows.
- This document describes dataset usage for running experiments and reproducing results.
- For dataset ownership, licensing, and usage terms, please refer to the original source pages.
