# D-HASH: Dynamic Hot-key Aware Scalable Hashing

[![Paper](https://img.shields.io/badge/SCIE-Accepted-0066CC?style=flat-square&logo=googlescholar&logoColor=white)]()
[![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?style=flat-square&logo=python&logoColor=white)]()
[![Redis](https://img.shields.io/badge/Redis-Cluster-DC382D?style=flat-square&logo=redis&logoColor=white)]()
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)

> **Official Implementation** of the paper *"D-HASH: Dynamic Hot-key Aware Scalable Hashing for Load Balancing in Distributed Cache Systems"*, accepted in **KSII Transactions on Internet and Information Systems (TIIS)**, 2026.
>
> **Author:** Hyeok Bang ([@bh1848](https://github.com/bh1848))

> 💡 **For Korean Visitors:** 실험 과정과 상세 분석은 [**기술 분석 및 실험 기록**](./docs/REPORT_KR.md)에서 확인하실 수 있습니다.    
<br>

## 📌 Project Overview
Hot-keys in distributed cache systems (e.g., Redis) cause severe **load imbalance**, leading to single-node bottlenecks.
**D-HASH** introduces a **dynamic routing layer** on top of Consistent Hashing to detect and redistribute hot-key traffic in real-time.

* **Problem:** Single node overload due to skewed traffic (Zipfian distribution).
* **Solution:** Client-side hot-key detection & Window-based dynamic routing.
* **Impact:** Reduced load standard deviation (imbalance) by **33.8%** compared to Consistent Hashing.

<br>

## 🏗️ Architecture
The system consists of a **Smart Client** (monitoring & routing) and a **Hashing Ring**.
When a hot-key is detected, requests are dynamically routed to an **Alternate Node** to offload the primary server.

![System Architecture](./docs/images/dhash_architecture.png)

<br>

## 💻 Key Logic
The implementation focuses on **memory efficiency** and **low latency**.
We used `__slots__` to minimize memory footprint during high-concurrency simulations.

~~~python
# src/dhash_experiments/algorithms.py

class DHash:
    # Memory optimization for large-scale simulation
    __slots__ = ("nodes", "T", "W", "reads", "alt", "ch")

    def get_node(self, key: Any, op: str = "read") -> str:
        # 1. Write Consistency: Always route to Primary
        if op == "write":
            return self._primary_safe(key)

        # 2. Hot-key Detection & Dynamic Routing
        cnt = self.reads.get(key, 0) + 1
        self.reads[key] = cnt
        
        # If hot-key, switch to Alternate Node based on Window Epoch
        if cnt >= self.T:
            self._ensure_alternate(key)
            delta = cnt - self.T
            epoch = (delta - self.W) // self.W
            # Round-Robin between Primary and Alternate
            return self.alt[key] if (epoch % 2 == 0) else self._primary_safe(key)

        return self._primary_safe(key)
~~~

<br>

## 🚀 Quick Start
Reproduce the benchmark results using Docker Compose.

~~~bash
# 1. Clone Repository
git clone https://github.com/bh1848/D-HASH.git
cd D-HASH

# 2. Run Simulation (Redis Cluster + Benchmark)
docker-compose up --build

# 3. Check Logs
docker-compose logs -f runner
~~~

<br>

## 📊 Benchmark Results
Experiments were conducted under a **High-Skew Zipfian Workload ($\alpha=1.5$)**.

| Algorithm | Throughput (ops/s) | Load Std Dev (Lower is better) | Improvement |
| :--- | :--- | :--- | :--- |
| Consistent Hashing (CH) | 179,902 | 49,944 | - |
| **D-HASH (Ours)** | 167,092 | **33,054** | **🔻 33.8%** |

> **Result:** D-HASH significantly improves load balancing (**33.8% lower Std Dev**) with minimal throughput overhead (~7%).

<br>

## 📝 Citation
If you use this code for your research, please cite our paper:

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

## 📧 Contact
For any questions, please contact **Hyeok Bang** at [bh1848@naver.com](mailto:bh1848@naver.com).
