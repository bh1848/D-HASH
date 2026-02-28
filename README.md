# D-HASH  
Dynamic Hot-key Aware Scalable Hashing

<p align="left">
  <img src="https://img.shields.io/badge/Python-3.11-3776AB?style=flat-square&logo=python&logoColor=white"/>
  <img src="https://img.shields.io/badge/Redis-7.4.2-DC382D?style=flat-square&logo=redis&logoColor=white"/>
  <img src="https://img.shields.io/badge/Docker-Ready-2496ED?style=flat-square&logo=docker&logoColor=white"/>
  <img src="https://img.shields.io/badge/TIIS_(SCIE)-Accepted_(In_Press)-0066CC?style=flat-square&logo=googlescholar&logoColor=white"/>
  <img src="https://img.shields.io/badge/License-MIT-green?style=flat-square"/>
</p>

> Client-side routing layer for mitigating hot-key load imbalance  
> Built on top of Consistent Hashing

This repository contains the implementation of:

**D-HASH: Dynamic Hot-key Aware Scalable Hashing for Load Balancing in Distributed Cache Systems**  
Accepted in *KSII Transactions on Internet and Information Systems (SCIE)*, 2026 (In Press).

For Korean engineering-focused documentation:  
👉 See [README_kr.md](./docs/README_kr.md)

---

## Motivation

Zipf-distributed workloads create hot-keys that concentrate traffic on a single node.  
Consistent Hashing preserves mapping stability but does not regulate read concentration.

D-HASH introduces:

- Client-side hot-key detection  
- Deterministic window-based routing  
- Separation of alternate selection and switching timing  

No server-side modification is required.

---

## Guard Phase (Implementation-Consistent Snippet)

The early-return condition is defined before this block in `get_node()`.

```python
delta = max(0, cnt - self.T)

if delta < self.W:
    return self._primary_safe(key)

epoch = (delta - self.W) // self.W
return self.alt[key] if (epoch % 2 == 0) else self._primary_safe(key)
```

Switching occurs only after the guard window.

---

## Measurement Alignment

In pipelined workloads, one latency sample may represent multiple operations.  
Percentile calculation is weighted by operation count.

```python
def _weighted_percentile(samples, q):
    samples_sorted = sorted(samples, key=lambda x: x[0])
    total_w = sum(w for _, w in samples_sorted)
    target = q * total_w
    ...
```

ConnectionPool reuse isolates connection variability from latency measurement.

---

## Architecture

![System Architecture](./docs/images/dhash_architecture.png)

---

## Experimental Snapshot (Zipf α=1.5)

| Algorithm | Throughput (ops/s) | Load Std Dev |
|-----------|-------------------|--------------|
| Consistent Hashing | 179,902 | 49,944 |
| D-HASH | 167,092 | 33,054 |

Experimental configuration is provided in the benchmark module.

---

## Reproducibility

```bash
git clone https://github.com/bh1848/D-HASH.git
cd D-HASH
docker-compose up --build
```

---

## Engineering Documentation

Detailed troubleshooting and design notes  
(Korean, engineering-focused):

- docs/troubleshooting/01_alternate_selection.md  
- docs/troubleshooting/02_guard_phase.md  
- docs/troubleshooting/03_routing_window.md  
- docs/troubleshooting/04_weighted_percentile.md  

---

## Citation

```bibtex
@article{bang2026dhash,
  title={D-HASH: Dynamic Hot-key Aware Scalable Hashing for Load Balancing in Distributed Cache Systems},
  author={Bang, Hyeok and Jeon, Sanghoon},
  journal={KSII Transactions on Internet and Information Systems},
  year={2026},
  note={Accepted, In Press}
}
```

---

## License

MIT License.
