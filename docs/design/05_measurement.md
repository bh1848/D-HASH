# 05 Measurement

Latency is measured per pipeline batch.

For each batch:

- Record start and end time (ns)
- Compute average latency per operation:
  batch_latency / batch_size

Percentiles:

- Use weighted percentile
- value = batch_avg_latency
- weight = batch_size

Load imbalance:

- Count requests per node
- Compute standard deviation across nodes
