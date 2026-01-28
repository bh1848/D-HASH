# D-HASH: Dynamic Hot-key Aware Scalable Hashing

[![Paper](https://img.shields.io/badge/Paper-SCIE%20Accepted-blue)](논문링크)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?logo=python&logoColor=white)]()
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)]()

> **Official Implementation** of the paper *"D-HASH: Dynamic Hot-key Aware Scalable Hashing for Load Balancing in Distributed Cache Systems"*, accepted in **KSII Transactions on Internet and Information Systems (TIIS)**, 2026.
>
> *This repository is maintained by the **first author** of the paper.*

> 💡 **Detailed Report:** Check out [**docs/REPORT_KR.md**](./docs/REPORT_KR.md) for troubleshooting logs, detailed architectural decisions, and full experimental records (in Korean).

<br>

## 📌 Abstract
This repository provides the **core implementation** of D-HASH, a novel hashing algorithm designed to solve the load imbalance problem caused by hot-keys in distributed cache systems.

**Key Features:**
- **Dynamic Detection:** Real-time identification of hot-keys based on access frequency using a client-side counter.
- **Scalable Hashing:** Adaptive redistribution of hot-keys to minimize server overload without full data migration.
- **High Performance:** Reduces load standard deviation (imbalance) by **up to 26.7%** in high-skew workloads compared to Consistent Hashing.

<br>

## 🔒 Scope of This Repository
This repository focuses on the **core logic of the D-HASH algorithm** and a lightweight simulation framework for verification.

Due to dataset licensing (NASA/eBay logs) and ongoing extensions of this work, the **raw datasets and full preprocessing pipelines are not publicly included**. However, the core algorithmic components (`algorithms.py`) and benchmark tools (`bench.py`) required to reproduce the results are fully provided.

<br>

## 🏗️ System Architecture
The overall architecture consists of a client-side agent for key monitoring and a hashing ring for data distribution.

![System Architecture](./docs/images/dhash_architecture.png)
*(Note: D-HASH adds a dynamic routing layer on top of the standard Consistent Hashing ring.)*

<br>

## 📂 Project Structure
~~~text
D-HASH/
├── src/
│   └── dhash_experiments/
│       ├── algorithms.py   # Core Algorithm (DHash class & Routing Logic)
│       ├── bench.py        # Benchmark & Metrics Collection
│       ├── cli.py          # Entry Point (Argument Parsing)
│       ├── config.py       # Configuration & Hyperparameters
│       ├── stages.py       # Experiment Stage Controller
│       └── workloads.py    # Zipfian Workload Generator
├── docs/                   # Experiment Reports & Figures
├── results/                # Benchmark Results (CSV) & Metadata
├── Dockerfile.runner       # Simulation Environment
├── docker-compose.yml      # Orchestration (Redis Cluster + Runner)
├── requirements.txt        # Python Dependencies
└── README.md
~~~

<br>

## 🚀 How to Run
You can run the simulation using Docker Compose to observe the load balancing effect.

### 1. Prerequisites
- **Docker** & **Docker Compose**
- (Optional) Python 3.9+ (if running locally without Docker)

### 2. Build & Run
The default command runs the **full experiment suite** (Pipeline Sweep → Ablation → Zipf Benchmark) using synthetic data.

~~~bash
# Clone this repository
git clone https://github.com/bh1848/D-HASH.git
cd D-HASH

# Build and Start Simulation
docker-compose up --build

# View Logs (Real-time output)
docker-compose logs -f runner
~~~

<br>

## 📊 Benchmark Result (Reproducible)

This experiment uses a **Synthetic Zipfian Workload** (Alpha=1.5, High Skew) generated in real-time to ensure full reproducibility without external dataset dependencies.

| Algorithm | Throughput (ops/s) | Load Std Dev (Lower is better) | Improvement |
| :--- | :--- | :--- | :--- |
| Consistent Hashing (CH) | 179,902 | 49,944 | - |
| **D-HASH (Ours)** | **167,092** | **33,054** | **🔻 33.8%** |

> **Key Finding:** In high-skew environments ($\alpha=1.5$), D-HASH reduces load imbalance (Standard Deviation) by **33.8%** compared to CH, with only a marginal 7% trade-off in throughput, demonstrating the efficiency of our dynamic routing strategy.

<br>

## 📝 Citation
If you find this code useful for your research, please cite our paper:

~~~bibtex
@article{bang2026dhash,
  title={D-HASH: Dynamic Hot-key Aware Scalable Hashing for Load Balancing in Distributed Cache Systems},
  author={Bang, Hyeok and Jeon, Sanghoon},
  journal={KSII Transactions on Internet and Information Systems},
  year={2026},
  publisher={KSII}
}
~~~

<br>

## 👤 Author
**Bang Hyeok**
- Dept. of Information Security, The University of Suwon
- GitHub: [@bh1848](https://github.com/bh1848)
- Contact: banghyeok@suwon.ac.kr
