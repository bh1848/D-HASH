# D-HASH: Dynamic Hot-key Aware Scalable Hashing for Load Balancing in Distributed Cache Systems

Official implementation of D-HASH.
Accepted in KSII Transactions on Internet and Information Systems (TIIS, SCIE), 2026.

D-HASH is a client-side routing strategy for distributed cache systems
that reduces node load imbalance by 33.8% compared to Consistent Hashing,
evaluated on NASA web log and eBay auction datasets.

This repository contains the routing implementation and Redis-based experiments with a modular backend-style architecture.

## Documentation

- [Project Documentation](docs/README.md)
- [Architecture](docs/architecture.md)
- [Algorithm](docs/algorithm.md)
- [Experiments](docs/experiments.md)

## Overview

The repository is organized into two layers:

- **`dhash`**: core routing library
- **`dhash_repro`**: experiment runner

This separation keeps the routing logic small and keeps benchmark code outside the core routing layer.

## Results

| Strategy | Load Std Dev | vs Consistent Hashing |
|---|---|---|
| Consistent Hashing | baseline | — |
| D-HASH | — | **33.8% reduction** |

Evaluated on NASA HTTP web log and eBay auction datasets.

## Repository Structure

```text
src/
  dhash/
    hashing/
    routing/
    config.py
    stats.py

  dhash_repro/
    __main__.py
    experiment.py
    benchmark/
    clients/
    config/
    persistence/
    workloads/
```

## Quick Start

Run the experiment environment with Docker:

```bash
docker compose up --build runner
```

Stop and remove containers:

```bash
docker compose down -v
```

## License

MIT License
