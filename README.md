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

- [대체 노드에도 preload 적용해서 nil 발생 해결하기](https://velog.io/@bh1848/%EB%8C%80%EC%B2%B4-%EB%85%B8%EB%93%9C%EC%97%90%EB%8F%84-preload-%EC%A0%81%EC%9A%A9%ED%95%B4%EC%84%9C-nil-%EB%B0%9C%EC%83%9D-%ED%95%B4%EA%B2%B0%ED%95%98%EA%B8%B0)
- [cold start와 파이프라인 경계 문제 해결하기](https://velog.io/@bh1848/cold-start%EC%99%80-%ED%8C%8C%EC%9D%B4%ED%94%84%EB%9D%BC%EC%9D%B8-%EA%B2%BD%EA%B3%84-%EB%AC%B8%EC%A0%9C-%ED%95%B4%EA%B2%B0%ED%95%98%EA%B8%B0)
- [주 노드와 대체 노드가 같은 물리 노드를 가리키는 문제 해결하기](https://velog.io/@bh1848/%EC%A3%BC-%EB%85%B8%EB%93%9C%EC%99%80-%EB%8C%80%EC%B2%B4-%EB%85%B8%EB%93%9C%EA%B0%80-%EA%B0%99%EC%9D%80-%EB%AC%BC%EB%A6%AC-%EB%85%B8%EB%93%9C%EB%A5%BC-%EA%B0%80%EB%A6%AC%ED%82%A4%EB%8A%94-%EB%AC%B8%EC%A0%9C-%ED%95%B4%EA%B2%B0%ED%95%98%EA%B8%B0)
- [노드 구성 변경 이후 stale 대체 노드가 남는 문제 해결하기](https://velog.io/@bh1848/%EB%85%B8%EB%93%9C-%EA%B5%AC%EC%84%B1-%EB%B3%80%EA%B2%BD-%EC%9D%B4%ED%9B%84-stale-%EB%8C%80%EC%B2%B4-%EB%85%B8%EB%93%9C%EA%B0%80-%EB%82%A8%EB%8A%94-%EB%AC%B8%EC%A0%9C-%ED%95%B4%EA%B2%B0%ED%95%98%EA%B8%B0)

## License

MIT License
