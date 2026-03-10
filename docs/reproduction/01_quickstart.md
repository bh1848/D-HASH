# Quickstart

## Overview

This document shows the shortest way to run the D-HASH benchmark environment.

The current project is designed to run through Docker.

---

## Prerequisites

Make sure the following tools are installed:

- Docker
- Docker Compose

No separate local CLI entry point is required for the normal benchmark flow.

---

## Run

Start the runner and Redis nodes with:

```bash
docker compose up --build runner
```

This command builds the runner image, starts the required Redis containers, and runs the selected experiment mode.

---

## Stop

Stop the containers and remove volumes with:

```bash
docker compose down -v
```

This resets the local benchmark environment.

---

## Runtime Variables

The main runtime variables are:

- `DHASH_MODE`
- `DHASH_ALPHA`
- `DHASH_REPEATS`
- `DHASH_DATASET`

These are usually set in `docker-compose.yml`.

---

## What Happens During Execution

The runner does the following:

1. loads the selected dataset or synthetic workload
2. builds the selected routing strategy
3. sends requests to Redis nodes
4. writes benchmark output files

---

## Next

For more detail, continue with:

- [02 Datasets](02_datasets.md)
- [03 Benchmark](03_benchmark.md)
- [04 Results Format](04_results_format.md)
