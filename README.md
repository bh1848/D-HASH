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

- [D-HASH a(k) preload 누락과 nil rate](https://velog.io/@bh1848/D-HASH-alternate-%EB%85%B8%EB%93%9C-preload%EC%99%80-%EC%8B%A4%ED%97%98-%EA%B3%B5%EC%A0%95%EC%84%B1) — `a(k)` preload 누락으로 nil rate 45.3%가 발생했고 실험 조건을 라우팅 구조에 맞게 수정해 0%로 개선
- [D-HASH alternate 선택과 물리 노드 중복 제거](https://velog.io/@bh1848/D-HASH-alternate-%EB%85%B8%EB%93%9C%EC%99%80-Consistent-Hashing-%EB%AC%BC%EB%A6%AC-%EB%85%B8%EB%93%9C-%EB%B6%84%EC%82%B0) — 가상 노드 기준 alternate 선택 시 약 20%의 key에서 `p(k)`와 `a(k)`가 같은 물리 노드를 가리키는 문제를 물리 노드 기준 dedup으로 해결, same physical 비율 20% → 0%로 개선
- [D-HASH guard phase와 cold start 해결](https://velog.io/@bh1848/D-HASH-%ED%8A%B8%EB%9F%AC%EB%B8%94%EC%8A%88%ED%8C%85-guard-phase%EC%99%80-epoch-offset-%EC%84%A4%EA%B3%84) — threshold 직후 cold start와 pipeline 경계 불일치 문제를 guard phase와 epoch 기반 window 전환으로 해결, guard phase `a(k)` 비율 60% → 0%로 개선
- [D-HASH 노드 변경 시 stale alternate 문제](https://velog.io/@bh1848/D-HASH%EC%97%90%EC%84%9C-%EB%85%B8%EB%93%9C%EA%B0%80-%EB%B0%94%EB%80%8C%EB%A9%B4-alt-%EC%BA%90%EC%8B%9C%EB%A5%BC-%EC%A0%84%EB%B6%80-%EB%B9%84%EC%9A%B0%EB%8A%94-%EC%9D%B4%EC%9C%A0) — membership change 시 영향받은 key 100%에서 stale alternate 발생, ring signature 기반 `alt.clear()`로 0%로 해소

## License

MIT License
