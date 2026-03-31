# D-HASH: Dynamic Hot-key Aware Scalable Hashing for Load Balancing in Distributed Cache Systems

Official implementation of D-HASH.<br>
Published in KSII Transactions on Internet and Information Systems (TIIS, SCIE), 2026. | [paper](https://bh1848.github.io/D-HASH/paper.html)<br>
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

> This repository refactors the paper implementation into the current project structure while preserving the core experimental semantics. Measured metrics may differ from the results reported in the paper depending on the execution environment.

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

## Troubleshooting

- [D-HASH alternate preload와 실험 공정성](https://velog.io/@bh1848/D-HASH-alternate-%EB%8D%B0%EC%9D%B4%ED%84%B0-%EA%B3%B5%EB%B0%B1-%EB%AC%B8%EC%A0%9C%EC%99%80-preload-%ED%99%95%EC%9E%A5)
- [D-HASH guard phase와 cold start 방지 설계](https://velog.io/@bh1848/D-HASH-%ED%8A%B8%EB%9F%AC%EB%B8%94%EC%8A%88%ED%8C%85-guard-phase%EC%99%80-epoch-offset-%EC%84%A4%EA%B3%84)
- [D-HASH alternate 물리 노드 중복 제거](https://velog.io/@bh1848/D-HASH-alternate-%EB%85%B8%EB%93%9C%EC%99%80-Consistent-Hashing-%EB%AC%BC%EB%A6%AC-%EB%85%B8%EB%93%9C-%EB%B6%84%EC%82%B0)
- [D-HASH 노드 변경 시 stale alternate 문제](https://velog.io/@bh1848/%EB%85%B8%EB%93%9C-%EB%B3%80%EA%B2%BD-%ED%9B%84-stale-alternate%EB%A1%9C-read-%EA%B2%BD%EB%A1%9C%EA%B0%80-%EC%98%A4%EC%97%BC%EB%90%98%EB%8A%94-%EB%AC%B8%EC%A0%9C)

## License

MIT License
