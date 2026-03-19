# Config Schema

## Overview

This document describes the environment variables used to run D-HASH experiments.

The current implementation exposes a small set of runtime options through environment variables.
Most other experiment defaults are defined in code.

---

## Runtime Variables

### `DHASH_MODE`

Selects which experiment stage to run.

Supported values:

- `all`
- `pipeline`
- `microbench`
- `zipf`
- `ablation`
- `redistrib`

Default:

```text
all
```

---

### `DHASH_ALPHA`

Controls the alpha value used when generating a Zipf workload.

This value is used in:

- `pipeline` mode
- `ablation` mode

In `zipf` mode, this variable is not used.
The implementation uses `DHASH_ZIPF_ALPHAS` when it is set, or the in-code default alpha sweep otherwise.

Default:

```text
1.5
```

---

### `DHASH_REPEATS`

Sets how many times each experiment is repeated.

This value is used to run the same benchmark multiple times with different random seeds.

Default:

```text
10
```

---

### `DHASH_DATASET_FILTER`

Selects which dataset set the experiment runner should execute.

Supported values:

- `nasa`
- `ebay`
- `all`

Default:

```text
ALL
```

`DHASH_DATASET` is still accepted as a legacy single-dataset selector.

---

### `DHASH_FIXED_WINDOW`

Overrides the dataset-specific default `W` used by zipf, microbench, and ablation stages.

---

### `DHASH_DHASH_T`

Overrides the dataset-specific default threshold `T` used in the main Zipf stage.

---

### `DHASH_PIPELINE_FOR_ZIPF`

Overrides the dataset-specific default pipeline size `B` used in the main Zipf stage.

---

### `DHASH_ZIPF_ALPHAS`

Overrides the default Zipf alpha sweep used in `zipf` mode.

Examples:

- `1.5`
- `1.1,1.3,1.5`

If unset, the implementation uses the in-code default sweep.

---

### `DHASH_ALGOS`

Selects the comparison set for applicable stages.

Supported values:

- `auto`
- `minimal`
- `all`
- `custom`

---

### `DHASH_ALGOS_LIST`

Comma-separated algorithm aliases used when `DHASH_ALGOS=custom`.

Supported aliases:

- `ch`
- `wch`
- `hrw`
- `dhash`

---

## Dataset Path Variables

The runner can load either a processed trace or a raw dataset file.

### NASA

- `DHASH_NASA_TRACE`: path to a processed NASA trace file
- `DHASH_NASA_RAW`: path to a raw NASA log file or zip file

### eBay

- `DHASH_EBAY_TRACE`: path to a processed eBay trace file
- `DHASH_EBAY_RAW`: path to a raw eBay csv file or zip file

If these variables are not set, the runner searches common data directories in the repository.
The repository search order prefers known raw dataset filenames before repository processed traces.

---

## In-Code Defaults

Some experiment values are not configured through environment variables.

Examples include:

- pipeline sweep values
- Zipf alpha sweep values
- ablation thresholds
- dataset-specific defaults for `B`, `W`, `T`, and `rho`
- Redis port (`REDIS_PORT`, default: 6379)

These defaults are defined in:

```text
src/dhash_repro/config/defaults.py
```

---

## Scope

This document only describes the runtime configuration currently used by the code.

It does not define a general configuration system beyond the variables and constants already implemented.
