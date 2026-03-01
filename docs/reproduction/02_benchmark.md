# 02 Benchmark

Parameters:

- nodes
- threshold (T)
- window (W)
- replicas
- num_ops
- num_keys
- alpha (Zipf)
- read_ratio
- pipeline
- repeats

Algorithms:

- ch
- wch
- hrw
- dhash
- all

Example:

```bash
python -m benchmarks.runner --algo dhash --repeats 3
```
