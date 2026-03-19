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
- `DHASH_DATASET_FILTER`
- `DHASH_DHASH_T`
- `DHASH_FIXED_WINDOW`
- `DHASH_PIPELINE_FOR_ZIPF`
- `DHASH_ZIPF_ALPHAS`
- `DHASH_ALGOS`
- `DHASH_ALGOS_LIST`

The repository root `docker-compose.yml` currently sets:

- `DHASH_MODE=all`
- `DHASH_ALPHA=1.5`
- `DHASH_REPEATS=1`

The code defaults are broader than the compose sample. For example, if `DHASH_REPEATS` is not set, the runner uses `10`.

---

## Examples

Run the default compose command:

```bash
docker compose up --build runner
```

Run a NASA-only Zipf experiment inside the running container:

```bash
docker compose exec runner sh -lc "DHASH_MODE=zipf DHASH_DATASET_FILTER=nasa DHASH_REPEATS=10 python -m dhash_repro"
```

Run only `alpha = 1.5` in Zipf mode:

```bash
docker compose exec runner sh -lc "DHASH_MODE=zipf DHASH_DATASET_FILTER=nasa DHASH_ZIPF_ALPHAS=1.5 DHASH_REPEATS=1 python -m dhash_repro"
```

Run the redistribution report:

```bash
docker compose exec runner sh -lc "DHASH_MODE=redistrib DHASH_DATASET_FILTER=all python -m dhash_repro"
```

---

## What Happens During Execution

The runner does the following:

1. loads the selected dataset base or creates the requested benchmark key set
2. builds the selected routing strategy
3. flushes Redis databases
4. preloads controlled-initialization data when needed
5. warms up sampled keys
6. sends measured requests to Redis nodes
7. writes benchmark output files

---

## Next

For more detail, continue with:

- [02 Datasets](02_datasets.md)
- [03 Benchmark](03_benchmark.md)
- [04 Results Format](04_results_format.md)
