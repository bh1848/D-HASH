# D-HASH: Dynamic Hot-key Aware Scalable Hashing

<p align="left">
  <img src="https://img.shields.io/badge/Python-3.11-3776AB?style=flat-square&logo=python&logoColor=white"/>
  <img src="https://img.shields.io/badge/Redis-7.4.2-DC382D?style=flat-square&logo=redis&logoColor=white"/>
  <img src="https://img.shields.io/badge/Docker-Ready-2496ED?style=flat-square&logo=docker&logoColor=white"/>
  <img src="https://img.shields.io/badge/TIIS_(SCIE)-In_Press-0066CC?style=flat-square&logo=googlescholar&logoColor=white"/>
  <img src="https://img.shields.io/badge/License-MIT-green?style=flat-square"/>
</p>

> **Official Implementation** of the paper: *"D-HASH: Dynamic Hot-key Aware Scalable Hashing for Load Balancing in Distributed Cache Systems"*, Accepted in **KSII TIIS**, 2026.

D-HASH is a lightweight, client-side routing layer built on top of Consistent Hashing to mitigate load imbalance caused by hot-keys in distributed cache systems.

[한국어 문서 바로가기](./docs/REPORT_KR.md)

<br/>

## 📌 Highlights
* **Problem**: Single-node bottlenecks due to skewed Zipfian traffic.
* **Solution**: Real-time hot-key detection & deterministic window-based routing.
* **Result**: **33.8% reduction** in load standard deviation with minimal (~7%) throughput overhead.

<br/>

## Architecture
![System Architecture](./docs/images/dhash_architecture.png)

<br/>

## Environment
| Category | Specification |
| :--- | :--- |
| **Hardware** | Intel Core i5-1340P, 16GB RAM |
| **OS** | Windows 11 (WSL2 Docker) |
| **Runtime** | Python 3.11.13 |
| **Stack** | Redis 7.4.2, redis-py 6.4.0, xxhash 3.6.0 

<br/>

## Core Logic: Guard Phase
D-HASH uses a **Guard Phase** to prevent "Cold Start" on alternate nodes by maintaining primary routing for the first window ($W$) after promotion.

~~~python
# src/dhash_experiments/algorithms.py

def get_node(self, key: Any, op: str = "read") -> str:
    if op == "write":
        return self._primary_safe(key)

    cnt = self.reads.get(key, 0) + 1
    self.reads[key] = cnt
    
    if cnt >= self.T:
        self._ensure_alternate(key)
        delta = cnt - self.T
        
        # Guard Phase: Stick to Primary for the first window W
        if delta < self.W:
            return self._primary_safe(key)
            
        # Window-based switching between Primary and Alternate
        epoch = (delta - self.W) // self.W
        return self.alt[key] if (epoch % 2 == 0) else self._primary_safe(key)

    return self._primary_safe(key)
~~~

<br/>

## Quick Start
~~~bash
git clone https://github.com/bh1848/D-HASH.git
cd D-HASH
docker-compose up --build
~~~

<br/>

## 📊 Evaluation (Zipf $\alpha=1.5$)
| Algorithm | Throughput (ops/s) | Load Std Dev (🔻) |
| :--- | :--- | :--- |
| Consistent Hashing | 179,902 | 49,944 |
| **D-HASH (Ours)** | **167,092** | **33,054 (33.8%↓)** |

<br/>


## Citation
~~~bibtex
@article{bang2026dhash,
  title={D-HASH: Dynamic Hot-key Aware Scalable Hashing for Load Balancing in Distributed Cache Systems},
  author={Bang, Hyeok and Jeon, Sanghoon},
  journal={KSII Transactions on Internet and Information Systems},
  year={2026},
  note={In Press}
}
~~~

<br/>

## Contact
For any questions regarding the algorithm or implementation, please contact:
* **Hyeok Bang**: [bh1848@naver.com](mailto:bh1848@naver.com)

<br/>

## License
This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for details.
