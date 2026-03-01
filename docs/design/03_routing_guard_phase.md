# 03 Routing — Guard Phase

Hot-key promotion occurs when read count >= T.

After promotion:

- A deterministic alternate node A(k) is selected.
- For the first W requests after promotion:
  - Reads remain routed to primary.
  - This allows cache warm-up on alternate.

Guard condition:

delta = read_count - T

If delta < W:
    route to primary
