# D-HASH

Dynamic Hot-key Aware Scalable Hashing

Client-side routing layer for mitigating hot-key load imbalance  
Built on top of Consistent Hashing

---

## Paper Snapshot

The implementation used for the TIIS 2026 (In Press) paper is preserved as a git tag.

```bash
git checkout tiis-2026-inpress
```

The `main` branch contains the actively maintained engineering structure.
Routing semantics defined in the paper are preserved unless explicitly versioned.

---

## Project Structure

- `src/dhash/` — Routing and hashing implementation
- `benchmarks/` — Benchmark runner and workload generators
- `tests/` — Unit tests
- `docs/` — Design, reproduction, and reference documentation
- `scripts/` — Helper scripts (lint, test, benchmark)

---

## Installation

```bash
pip install -e ".[dev]"
```

---

## Benchmark

```bash
python -m benchmarks.runner --help
```

---

## Documentation

- English documentation: `docs/README.md`
- Korean documentation: `docs/README_kr.md`

---

## License

MIT License.
