# 01. Quickstart

This document describes how to execute experiments.

The reproduction layer is implemented under:

`src/dhash_repro/`

---

## Requirements

- Python >= 3.11
- Docker
- Docker Compose

---

## Environment Setup

Start the Redis-based experiment environment:

```bash
make docker-up
```

Equivalent:

```bash
docker-compose up --build
```

---

## Install Dependencies

```bash
make install
```

Installs the core package and development dependencies.

---

## Run Experiments

Run all experiment modes:

```bash
make repro
```

Equivalent:

```bash
dhash-repro --mode all
```

---

## Shutdown Environment

```bash
make docker-down
```

Equivalent:

```bash
docker-compose down -v
```
