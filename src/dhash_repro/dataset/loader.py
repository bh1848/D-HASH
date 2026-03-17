import csv
import logging
import os
import re
import zipfile
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

from dhash_repro.config.defaults import DATASET_DEFAULTS, DEFAULT_DATASET

logger = logging.getLogger(__name__)

_CLF_RE = re.compile(
    r"^(?P<host>\S+) \S+ \S+ \[(?P<time>.*?)\] "
    r'"(?P<method>\S+)\s+(?P<url>\S+)\s+(?P<proto>[^"]+)" '
    r"(?P<status>\d{3}) (?P<size>\S+)"
)


def resolve_dataset() -> str:
    dataset = os.getenv("DHASH_DATASET", DEFAULT_DATASET).strip().lower()
    if dataset not in DATASET_DEFAULTS:
        raise ValueError(
            f"Unsupported dataset: {dataset}. Expected one of {sorted(DATASET_DEFAULTS)}"
        )
    return dataset


def _trace_env_var(dataset: str) -> str:
    return f"DHASH_{dataset.upper()}_TRACE"


def _raw_env_var(dataset: str) -> str:
    return f"DHASH_{dataset.upper()}_RAW"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _package_data_root() -> Path:
    return Path(__file__).resolve().parents[1] / "data"


def _data_roots() -> List[Path]:
    roots = [
        Path.cwd() / "data",
        _repo_root() / "data",
        _package_data_root(),
    ]

    seen = set()
    ordered: List[Path] = []
    for root in roots:
        key = str(root.resolve()) if root.exists() else str(root)
        if key not in seen:
            seen.add(key)
            ordered.append(root)
    return ordered


def _candidate_paths(dataset: str) -> List[Path]:
    candidates: List[Path] = []

    raw_env = os.getenv(_raw_env_var(dataset), "").strip()
    if raw_env:
        candidates.append(Path(raw_env))

    trace_env = os.getenv(_trace_env_var(dataset), "").strip()
    if trace_env:
        candidates.append(Path(trace_env))

    for data_root in _data_roots():
        if dataset == "nasa":
            candidates.extend(
                [
                    data_root / "processed" / "nasa_trace.txt",
                    data_root / "raw" / "nasa_http_logs.zip",
                    data_root / "raw" / "nasa_http_logs.log",
                ]
            )
        elif dataset == "ebay":
            candidates.extend(
                [
                    data_root / "processed" / "ebay_trace.txt",
                    data_root / "raw" / "ebay_auction_logs.csv",
                    data_root / "raw" / "ebay_auction_logs.zip",
                ]
            )

    cwd = Path.cwd()
    if dataset == "nasa":
        candidates.extend(
            [
                cwd / "nasa_trace.txt",
                cwd / "nasa_http_logs.zip",
                cwd / "nasa_http_logs.log",
            ]
        )
    elif dataset == "ebay":
        candidates.extend(
            [
                cwd / "ebay_trace.txt",
                cwd / "ebay_auction_logs.csv",
                cwd / "ebay_auction_logs.zip",
            ]
        )

    seen = set()
    uniq: List[Path] = []
    for p in candidates:
        key = str(p.resolve()) if p.exists() else str(p)
        if key not in seen:
            seen.add(key)
            uniq.append(p)
    return uniq


def _load_ranked_keys_from_trace(trace_path: str) -> Tuple[List[str], int]:
    counts: Counter[str] = Counter()
    total_requests = 0

    with open(trace_path, "r", encoding="utf-8") as f:
        for raw in f:
            key = raw.strip()
            if not key:
                continue
            counts[key] += 1
            total_requests += 1

    if not counts:
        raise ValueError(f"Trace file is empty: {trace_path}")

    ranked_keys = [key for key, _ in counts.most_common()]
    return ranked_keys, total_requests


def _iter_nasa_log_lines(path: Path) -> Iterable[str]:
    if path.suffix.lower() == ".zip":
        with zipfile.ZipFile(path, "r") as zf:
            names = [n for n in zf.namelist() if not n.endswith("/")]
            if not names:
                raise ValueError(f"No file found inside NASA zip: {path}")
            log_name = next((n for n in names if n.lower().endswith(".log")), names[0])
            with zf.open(log_name, "r") as fp:
                for raw in fp:
                    yield raw.decode("ISO-8859-1", errors="ignore")
    else:
        with open(path, "r", encoding="ISO-8859-1", errors="ignore") as f:
            for line in f:
                yield line


def _load_ranked_keys_from_nasa_raw(path: str) -> Tuple[List[str], int]:
    counts: Counter[str] = Counter()
    total_requests = 0

    for line in _iter_nasa_log_lines(Path(path)):
        m = _CLF_RE.match(line.strip())
        if not m:
            continue
        url = m.group("url")
        if not url:
            continue
        counts[url] += 1
        total_requests += 1

    if not counts:
        raise ValueError(f"No valid NASA URL keys parsed from: {path}")

    ranked_keys = [key for key, _ in counts.most_common()]
    return ranked_keys, total_requests


def _iter_csv_rows(path: Path) -> Iterable[Dict[str, str]]:
    if path.suffix.lower() == ".zip":
        with zipfile.ZipFile(path, "r") as zf:
            names = [n for n in zf.namelist() if not n.endswith("/")]
            if not names:
                raise ValueError(f"No file found inside CSV zip: {path}")
            csv_name = next((n for n in names if n.lower().endswith(".csv")), names[0])
            with zf.open(csv_name, "r") as fp:
                import io

                text_fp = io.TextIOWrapper(fp, encoding="utf-8-sig", newline="")
                reader = csv.DictReader(text_fp)
                for row in reader:
                    yield row
    else:
        with open(path, "r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                yield row


def _load_ranked_keys_from_ebay_raw(
    path: str, key_column: str = "auctionid"
) -> Tuple[List[str], int]:
    counts: Counter[str] = Counter()
    total_requests = 0

    for row in _iter_csv_rows(Path(path)):
        raw_key = row.get(key_column)
        key = raw_key.strip() if raw_key is not None else ""
        if not key:
            continue
        counts[key] += 1
        total_requests += 1

    if not counts:
        raise ValueError(f"No valid eBay keys parsed from: {path}")

    ranked_keys = [key for key, _ in counts.most_common()]
    return ranked_keys, total_requests


def load_dataset_workload_base(dataset: str) -> Tuple[List[str], int]:
    trace_env = _trace_env_var(dataset)
    raw_env = _raw_env_var(dataset)

    trace_path = os.getenv(trace_env, "").strip()
    if trace_path:
        logger.info("[%s] Loading processed trace from %s", dataset, trace_path)
        return _load_ranked_keys_from_trace(trace_path)

    for candidate in _candidate_paths(dataset):
        if not candidate.exists():
            continue

        suffix = candidate.suffix.lower()

        if dataset == "nasa":
            if suffix == ".txt":
                logger.info("[%s] Loading processed trace from %s", dataset, candidate)
                return _load_ranked_keys_from_trace(str(candidate))
            if suffix in {".zip", ".log"}:
                logger.info("[%s] Loading raw NASA dataset from %s", dataset, candidate)
                return _load_ranked_keys_from_nasa_raw(str(candidate))

        elif dataset == "ebay":
            if suffix == ".txt":
                logger.info("[%s] Loading processed trace from %s", dataset, candidate)
                return _load_ranked_keys_from_trace(str(candidate))
            if suffix in {".csv", ".zip"}:
                logger.info("[%s] Loading raw eBay dataset from %s", dataset, candidate)
                return _load_ranked_keys_from_ebay_raw(str(candidate))

    raise ValueError(
        f"No dataset input found for '{dataset}'. "
        f"Use {trace_env} for a processed trace, or {raw_env} for a raw dataset. "
        f"Searched under: {[str(root) for root in _data_roots()]}"
    )
