import argparse
import hashlib
import json
import re
import zipfile
from collections import Counter
from pathlib import Path
from typing import Iterator


_CLF_RE = re.compile(
    r"^(?P<host>\S+) \S+ \S+ \[(?P<time>.*?)\] "
    r'"(?P<method>\S+)\s+(?P<url>\S+)\s+(?P<proto>[^"]+)" '
    r"(?P<status>\d{3}) (?P<size>\S+)"
)


def iter_lines(path: Path) -> Iterator[str]:
    if path.suffix.lower() == ".zip":
        with zipfile.ZipFile(path, "r") as zf:
            names = [n for n in zf.namelist() if not n.endswith("/")]
            if not names:
                raise ValueError(f"No file found inside zip: {path}")
            log_name = next((n for n in names if n.lower().endswith(".log")), names[0])
            with zf.open(log_name, "r") as fp:
                for raw in fp:
                    yield raw.decode("ISO-8859-1", errors="ignore")
    else:
        with open(path, "r", encoding="ISO-8859-1", errors="ignore") as f:
            for line in f:
                yield line


def sha256_of_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--manifest", required=False)
    args: argparse.Namespace = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    counts: Counter[str] = Counter()
    total_rows = 0

    with open(output_path, "w", encoding="utf-8") as out:
        for line in iter_lines(input_path):
            m = _CLF_RE.match(line.strip())
            if not m:
                continue
            url = m.group("url")
            if not url:
                continue
            out.write(url + "\n")
            counts[url] += 1
            total_rows += 1

    manifest = {
        "dataset": "nasa",
        "input": str(input_path),
        "output": str(output_path),
        "valid_rows": total_rows,
        "unique_keys": len(counts),
        "sha256": sha256_of_file(output_path),
    }

    if args.manifest:
        manifest_path = Path(args.manifest)
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2)

    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
