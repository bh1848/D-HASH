import csv
import io
import logging
import os
import re
import zipfile
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from dhash_repro.config.defaults import DATASET_DEFAULTS, DEFAULT_DATASET

logger = logging.getLogger(__name__)
_NASA_ZIP_PREFERRED_FILES = ("access.log", "nasa_http_logs.log")
_EBAY_ZIP_PREFERRED_FILES = ("auction.csv", "ebay_auction_logs.csv")

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
                    data_root / "raw" / "nasa_http_logs.zip",
                    data_root / "raw" / "nasa_http_logs.log",
                    data_root / "nasa_http_logs.zip",
                    data_root / "nasa_http_logs.log",
                    data_root / "processed" / "nasa_trace.txt",
                ]
            )
        elif dataset == "ebay":
            candidates.extend(
                [
                    data_root / "raw" / "ebay_auction_logs.csv",
                    data_root / "raw" / "ebay_auction_logs.zip",
                    data_root / "ebay_auction_logs.csv",
                    data_root / "ebay_auction_logs.zip",
                    data_root / "processed" / "ebay_trace.txt",
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


def _load_keys_from_trace(trace_path: str) -> Tuple[List[str], int]:
    keys: List[str] = []

    with open(trace_path, "r", encoding="utf-8") as f:
        for raw in f:
            key = raw.strip()
            if key:
                keys.append(key)

    if not keys:
        raise ValueError(f"Trace file is empty: {trace_path}")

    return keys, len(keys)


def _pick_zip_member(
    zf: zipfile.ZipFile,
    *,
    preferred_names: Tuple[str, ...],
    required_suffix: str,
    dataset_label: str,
    source_path: Path,
) -> str:
    names = [name for name in zf.namelist() if not name.endswith("/")]
    if not names:
        raise ValueError(f"No file found inside {dataset_label} zip: {source_path}")

    lower_to_name = {name.lower(): name for name in names}
    for preferred in preferred_names:
        chosen = lower_to_name.get(preferred.lower())
        if chosen is not None:
            return chosen

    suffix_matches = [name for name in names if name.lower().endswith(required_suffix.lower())]
    if len(suffix_matches) == 1:
        return suffix_matches[0]
    if len(suffix_matches) > 1:
        raise ValueError(
            f"Multiple {dataset_label} candidates found inside zip {source_path}: {suffix_matches}. "
            f"Rename the desired file or set an explicit raw input path."
        )

    raise ValueError(
        f"No {required_suffix} file found inside {dataset_label} zip: {source_path}. "
        f"Expected one of {preferred_names} or a single *{required_suffix} file."
    )


def _iter_nasa_log_lines(path: Path) -> Iterable[str]:
    if path.suffix.lower() == ".zip":
        with zipfile.ZipFile(path, "r") as zf:
            log_name = _pick_zip_member(
                zf,
                preferred_names=_NASA_ZIP_PREFERRED_FILES,
                required_suffix=".log",
                dataset_label="NASA",
                source_path=path,
            )
            with zf.open(log_name, "r") as fp:
                for raw in fp:
                    yield raw.decode("ISO-8859-1", errors="ignore")
    else:
        with open(path, "r", encoding="ISO-8859-1", errors="ignore") as f:
            for line in f:
                yield line


def load_logs_dataset(path: str) -> Tuple[List[Any], Dict[str, Any]]:
    keys: List[str] = []
    meta: Dict[str, Any] = {}

    for line in _iter_nasa_log_lines(Path(path)):
        m = _CLF_RE.match(line.strip())
        if not m:
            continue
        url = m.group("url")
        status = int(m.group("status"))
        if not url or status == 0:
            continue
        keys.append(url)
        meta.setdefault(url, []).append(
            {
                "host": m.group("host"),
                "timestamp": m.group("time"),
                "method": m.group("method"),
                "protocol": m.group("proto"),
                "status": status,
                "size": m.group("size"),
            }
        )

    if not keys:
        raise ValueError(f"No valid NASA URL keys parsed from: {path}")

    return keys, meta


def _iter_csv_rows(path: Path) -> Iterable[Dict[str, str]]:
    if path.suffix.lower() == ".zip":
        with zipfile.ZipFile(path, "r") as zf:
            csv_name = _pick_zip_member(
                zf,
                preferred_names=_EBAY_ZIP_PREFERRED_FILES,
                required_suffix=".csv",
                dataset_label="CSV",
                source_path=path,
            )
            with zf.open(csv_name, "r") as fp:
                text_fp = io.TextIOWrapper(fp, encoding="utf-8-sig", newline="")
                reader = csv.DictReader(text_fp)
                for row in reader:
                    yield row
    else:
        with open(path, "r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                yield row


def load_csv_dataset(
    path: str,
    key_column: str = "auctionid",
    natural_hot_threshold: Optional[int] = None,
) -> Tuple[List[Any], Dict[str, Any]]:
    rows = list(_iter_csv_rows(Path(path)))

    if not rows:
        raise ValueError(f"No valid eBay rows parsed from: {path}")
    if key_column not in rows[0]:
        raise ValueError(f"'{key_column}' column not found in CSV.")

    counts: Dict[str, int] = {}
    meta: Dict[str, List[Dict[str, str]]] = {}
    for row in rows:
        raw_key = row.get(key_column)
        key = raw_key.strip() if raw_key is not None else ""
        if not key:
            continue
        counts[key] = counts.get(key, 0) + 1
        meta.setdefault(key, []).append(row)

    if natural_hot_threshold is None:
        keys = sorted(counts.keys())
    else:
        keys = sorted(key for key, count in counts.items() if count <= natural_hot_threshold)

    return keys, meta


def load_dataset_workload_base(dataset: str) -> Tuple[List[str], int]:
    trace_env = _trace_env_var(dataset)
    raw_env = _raw_env_var(dataset)

    trace_path = os.getenv(trace_env, "").strip()
    if trace_path:
        logger.info("[%s] Loading processed trace from %s", dataset, trace_path)
        return _load_keys_from_trace(trace_path)

    for candidate in _candidate_paths(dataset):
        if not candidate.exists():
            continue

        suffix = candidate.suffix.lower()

        if dataset == "nasa":
            if suffix == ".txt":
                logger.info("[%s] Loading processed trace from %s", dataset, candidate)
                return _load_keys_from_trace(str(candidate))
            if suffix in {".zip", ".log"}:
                logger.info("[%s] Loading raw NASA dataset from %s", dataset, candidate)
                keys, _ = load_logs_dataset(str(candidate))
                return [str(key) for key in keys], len(keys)

        elif dataset == "ebay":
            if suffix == ".txt":
                logger.info("[%s] Loading processed trace from %s", dataset, candidate)
                return _load_keys_from_trace(str(candidate))
            if suffix in {".csv", ".zip"}:
                logger.info("[%s] Loading raw eBay dataset from %s", dataset, candidate)
                keys, _ = load_csv_dataset(str(candidate), natural_hot_threshold=None)
                return [str(key) for key in keys], len(keys)

    raise ValueError(
        f"No dataset input found for '{dataset}'. "
        f"Use {trace_env} for a processed trace, or {raw_env} for a raw dataset. "
        f"Searched under: {[str(root) for root in _data_roots()]}"
    )
