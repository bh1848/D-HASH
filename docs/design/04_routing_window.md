# 04 Routing — Window Alternation

After guard phase:

- Requests are partitioned into windows of size W.
- Epoch e = floor(delta / W)

Routing rule:

- Even epoch: route to alternate
- Odd epoch: route to primary

This produces deterministic oscillation between nodes.

Writes are always routed to primary.
