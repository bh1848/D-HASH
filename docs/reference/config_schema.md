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
- `zipf`
- `ablation`

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

In `zipf` mode, the implementation uses the fixed values defined in code instead of this variable.

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
1
```

---

### `DHASH_DATASET`

Selects the dataset used by the experiment runner.

Supported values:

- `nasa`
- `ebay`

Default:

```text
nasa
```

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

---

## In-Code Defaults

Some experiment values are not configured through environment variables.

Examples include:

- pipeline sweep values
- Zipf alpha sweep values
- ablation thresholds
- dataset-specific defaults for `B`, `W`, `T`, and `rho`

These defaults are defined in:

```text
src/dhash_repro/config/defaults.py
```

---

## Scope

This document only describes the runtime configuration currently used by the code.

It does not define a general configuration system beyond the variables and constants already implemented.
