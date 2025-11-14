D-HASH Experiment Framework  
Redis-based Key Routing Evaluation Suite

This repository provides a reproducible framework for evaluating key–routing algorithms in a Redis-based multi-node setup. The implementation includes Consistent Hashing (CH), Weighted Consistent Hashing (WCH), Rendezvous Hashing (HRW), and D-HASH (Dynamic Hot-key Aware Scalable Hashing). The evaluation follows a multi-stage structure commonly used in systems research.

----------------------------------------------------------------------
Directory Structure
----------------------------------------------------------------------

```text
.
├── docker-compose.yml
├── Dockerfile.runner
├── requirements.txt
├── src/
│   └── dhash_experiments/
│       ├── cli.py
│       ├── stages.py
│       ├── algorithms.py
│       ├── workloads.py
│       ├── bench.py
│       ├── config.py
│       └── utils.py
├── data/                  (raw datasets, ignored in Git)
│   ├── nasa_http_logs.log
│   └── ebay_auction_logs.csv
└── results/               (generated outputs)
    └── .gitkeep
```
----------------------------------------------------------------------
System Requirements
----------------------------------------------------------------------

- Docker and Docker Compose
- Python 3.11 (inside runner container)
- Redis 7.4.2 (automatically pulled via docker-compose)
- At least 8 GB RAM recommended
- Tested on Windows 11 + WSL2; Linux and macOS also supported

----------------------------------------------------------------------
Building and Running
----------------------------------------------------------------------

(1) Build the runner image  
    docker compose build runner

(2) Start Redis cluster and runner  
    docker compose up -d

(3) Run all experiments  
    docker compose run --rm runner

(4) Run a specific stage  
    docker compose run --rm runner \
      python -m dhash_experiments.cli --mode <stage> --dataset <dataset>

Modes: all, pipeline, microbench, ablation, zipf, redistrib  
Datasets: NASA, eBay, ALL

----------------------------------------------------------------------
Experiment Stages
----------------------------------------------------------------------

A1. Pipeline Sweep  
    Evaluates pipeline sizes (B) and identifies B* that balances throughput and tail latency.

A2. Microbench  
    Measures pure routing cost (ns/op) without Redis I/O.  
    D-HASH reports cold and hot phases.

B. Threshold Ablation  
    Sensitivity analysis over threshold T with fixed R=2 and window W.

C. Zipf Workload Evaluation  
    Runs α ∈ {1.1, 1.3, 1.5}.  
    Reports throughput, average latency, p95, p99, and load standard deviation.

Redistribution  
    Reports key movement ratio (%) for membership transitions 5→6 and 6→5.

----------------------------------------------------------------------
Output Files
----------------------------------------------------------------------

All results are placed under results/ as CSV files:

{dataset}_pipeline_sweep.csv  
{dataset}_microbench_ns.csv  
{dataset}_ablation_results.csv  
{dataset}_zipf_results.csv  
{dataset}_redistribution.csv  
{dataset}_*_env_meta.csv

----------------------------------------------------------------------
Reproducibility Notes
----------------------------------------------------------------------

- Seeds: SEED=1337, PYTHONHASHSEED=123  
- Redis configuration: appendonly no, save ""  
- Five isolated nodes (equal CPU/memory limits)  
- Warmup batches excluded  
- All metrics reported as mean ± standard deviation

----------------------------------------------------------------------
License
----------------------------------------------------------------------

MIT License
