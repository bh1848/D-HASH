# D-HASH

Dynamic Hot-key Aware Scalable Hashing

A client-side routing layer designed to mitigate load imbalance caused by hot-keys.
Built on top of Consistent Hashing with dynamic re-routing capabilities.

---

## Paper Snapshot

The implementation used for the **TIIS 2026 (In Press)** paper is preserved as a git tag.

```bash
git checkout tiis-2026-inpress
```

The `main` branch contains the actively maintained engineering structure.
Routing semantics defined in the paper are strictly preserved unless explicitly versioned.

---

## Project Structure

- `src/dhash/` — Core library (Routing and hashing implementation)
- `src/dhash_repro/` — Experiment harness and reproduction workloads
- `tests/` — Unit tests mirrored from `src/dhash`
- `docs/` — Design, reproduction, and reference documentation
- `Makefile` — Unified entry point for development and reproduction tasks

---

## Installation

All dependencies for both the core library and reproduction environment are managed via `pyproject.toml`. This ensures environment consistency without the need for fragmented `requirements.txt` files.

```bash
# Install core library and all development/reproduction dependencies
make install
```

*Note: This command installs the package in editable mode (`-e`) along with `pandas`, `numpy`, `redis`, and necessary dev tools.*

---

## Benchmark & Reproduction

You can execute the full suite of experiments using the unified CLI or the provided `Makefile`.

```bash
# Run all experimental stages (Pipeline sweep, Zipf analysis, etc.)
make repro

# Or use the CLI directly for specific configurations
dhash-repro --mode zipf --repeats 10
```

---

## Development Workflow

Maintain code quality and consistency using the following standardized commands:

```bash
make check   # Run formatter, linter, type-checker, and unit tests
make test    # Run unit tests only
make format  # Auto-format code using Ruff
```

---

## Documentation

- [English Documentation](docs/README.md)
- [Korean Documentation](docs/README_kr.md)

---

## License

MIT License.
