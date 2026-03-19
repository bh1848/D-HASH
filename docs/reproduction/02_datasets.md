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

> Raw dataset files may be provided locally under `data/raw`, but they are not guaranteed in every checkout or distribution of this repository.
> If they are absent, please download them directly from the original source pages and review the applicable terms or license information before use.

---

## NASA

The NASA dataset is used as an HTTP-style request trace.

The runner can load:

- a processed trace file
- a raw log file
- a raw zip file

If `DHASH_NASA_TRACE` is set explicitly, the runner uses it directly.
Otherwise, the repository search order prefers known raw dataset filenames before repository processed traces.

---

## eBay

The eBay dataset is used as a second real-world style workload.

The runner can load:

- a processed trace file
- a raw CSV file
- a raw zip file

If `DHASH_EBAY_TRACE` is set explicitly, the runner uses it directly.
Otherwise, the repository search order prefers known raw dataset filenames before repository processed traces.

---

## Current Parsing Semantics

- NASA raw input is parsed as a request sequence of URL keys from CLF-style log lines.
- eBay raw input is parsed as `auctionid` keys and then reduced to a sorted unique-key base.
- Processed trace files are read as plain text, one key per line.

---

## Dataset Selection

The active dataset can be selected through either:

```text
DHASH_DATASET_FILTER
```

Supported values are:

- `nasa`
- `ebay`
- `all`

`DHASH_DATASET` is still accepted as a legacy single-dataset selector.

The runner resolves the corresponding processed or raw path from the configured environment variables or the default data directories.

---

## Scope

- Processed traces are useful when you want an explicit fixed input file.
- Raw datasets are fully supported by the current runner and are often the default resolution path in repository-based execution.
- This document describes dataset usage for running experiments and reproducing results.
- For dataset ownership, licensing, and usage terms, please refer to the original source pages.
