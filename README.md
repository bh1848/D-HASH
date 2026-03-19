# D-HASH: Dynamic Hot-key Aware Scalable Hashing for Load Balancing in Distributed Cache Systems

Official implementation of D-HASH.<br>
Accepted in KSII Transactions on Internet and Information Systems (TIIS, SCIE), 2026.<br>
**Hyeok Bang**\*, Sanghoon Jeon (*first author)

D-HASH is a client-side routing strategy for distributed cache systems that reduces node load imbalance by up to 26.7% compared to Consistent Hashing, evaluated on NASA HTTP web log and eBay auction datasets.

## Overview

The repository is organized into two layers:

- **`dhash`**: core routing library
- **`dhash_repro`**: experiment runner

This separation keeps the routing logic small and keeps benchmark code outside the core routing layer.

## Results

Load Stddev reduction on NASA HTTP web log (Zipf α = 1.1–1.5, 5 Redis nodes):

| Strategy | α = 1.1 | α = 1.3 | α = 1.5 |
|---|---|---|---|
| Consistent Hashing | 292,652 | 523,446 | 725,757 |
| Weighted CH | 297,534 | 525,973 | 726,973 |
| Rendezvous (HRW) | 311,019 | 466,891 | 623,144 |
| **D-HASH** | **228,827** | **387,997** | **531,824** |

D-HASH reduces Load Stddev by 21.8–26.7% compared to Consistent Hashing on the NASA dataset. On the eBay dataset, where baseline load variability is low, D-HASH maintains comparable performance without degradation.

## Quick Start

Run the experiment environment with Docker:
```bash
docker compose up --build runner
```

Stop and remove containers:
```bash
docker compose down -v
```

Run a specific stage inside the already-started runner container:
```bash
docker compose exec runner sh -lc "DHASH_MODE=zipf DHASH_DATASET_FILTER=nasa DHASH_REPEATS=10 python -m dhash_repro"
```

Supported stages in the current codebase are:

- `pipeline`
- `microbench`
- `zipf`
- `ablation`
- `redistrib`
- `all`

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
    benchmark/
    clients/
    config/
    experiment/
    persistence/
    workloads/
```

## Documentation

- [Project Documentation](docs/README.md)
- [Architecture](docs/architecture.md)
- [Algorithm](docs/algorithm.md)
- [Experiments](docs/experiments.md)

## License

MIT License
