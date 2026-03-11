# D-HASH: Dynamic Hot-key Aware Scalable Hashing for Load Balancing in Distributed Cache Systems

Official implementation of D-HASH.
Accepted in KSII Transactions on Internet and Information Systems (TIIS, SCIE), 2026.

D-HASH is a routing strategy for reducing load imbalance in distributed cache systems.

This repository contains the routing implementation and Redis-based experiments with a modular backend-style architecture.

## Quick Start

Run the experiment environment with Docker:

```bash
docker compose up --build runner
```

Stop and remove containers:

```bash
docker compose down -v
```

## Documentation

- [Project Documentation](docs/README.md)
- [Architecture](docs/architecture.md)
- [Algorithm](docs/algorithm.md)
- [Experiments](docs/experiments.md)

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

## Overview

The repository is organized into two layers:

- **`dhash`**: core routing library
- **`dhash_repro`**: experiment runner

This separation keeps the routing logic small and keeps benchmark code outside the core routing layer.

## License

MIT License
