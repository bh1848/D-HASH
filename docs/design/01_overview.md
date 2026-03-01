# 01 Overview

This document describes the structural components of D-HASH.

D-HASH consists of three layers:

1. Hashing Layer
   - Consistent Hashing ring
   - Virtual nodes (replicas)
   - Deterministic primary resolution

2. Routing Layer
   - Hot-key detection (threshold T)
   - Guard phase
   - Window-based alternation
   - Deterministic alternate selection

3. Measurement Layer
   - Batch-based latency measurement
   - Weighted percentile aggregation
   - Load imbalance statistics

The implementation separates these concerns into:

- `hashing.py`
- `routing/*`
- `measure/*`

The main branch preserves the routing semantics defined in the TIIS paper.
