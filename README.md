# D-HASH

Dynamic Hot-key Aware Scalable Hashing

Client-side routing layer for mitigating hot-key–induced load imbalance.
Artifact repository for the accepted TIIS (SCIE) journal paper.

---

## Status

Accepted at TIIS (SCIE).
Publication pending.

---

## Quick Start

### Requirements

- Python >= 3.11
- Docker
- Docker Compose

---

### Install (Local Development)

```bash
make install
```

This also installs pre-commit hooks.

---

### Experiment Environment (Docker)

Bring up the Redis-based reproduction environment:

```bash
make docker-up
```

Equivalent direct command:

```bash
docker-compose up --build
```

Stop and remove containers and volumes:

```bash
make docker-down
```

Equivalent direct command:

```bash
docker-compose down -v
```

---

### Run Experiments

```bash
make repro
```

Equivalent CLI:

```bash
dhash-repro --mode all
```

CLI options:

```bash
dhash-repro --mode {all|pipeline|zipf|ablation} --alpha 1.5 --repeats 10
```

---

## Structure

- `src/dhash/` — Core hashing and routing logic
- `src/dhash_repro/` — Experiment runner
- `tests/` — Unit tests
- `docs/` — Design and troubleshooting documentation

---

## Documentation

- [English Documentation](docs/README.md)
- [Korean Documentation](docs/README_kr.md)

---

## License

MIT License
