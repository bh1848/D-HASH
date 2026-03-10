import argparse
import csv
import hashlib
import io
import json
import zipfile
from collections import Counter
from pathlib import Path
from typing import Dict, Iterator


def iter_rows(path: Path) -> Iterator[Dict[str, str]]:
    if path.suffix.lower() == ".zip":
        with zipfile.ZipFile(path, "r") as zf:
            names = [n for n in zf.namelist() if not n.endswith("/")]
            if not names:
                raise ValueError(f"No file found inside zip: {path}")
            csv_name = next((n for n in names if n.lower().endswith(".csv")), names[0])
            with zf.open(csv_name, "r") as fp:
                text_fp = io.TextIOWrapper(fp, encoding="utf-8-sig", newline="")
                reader = csv.DictReader(text_fp)
                for row in reader:
                    yield {k: (v if v is not None else "") for k, v in row.items()}
    else:
        with open(path, "r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                yield {k: (v if v is not None else "") for k, v in row.items()}


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
    parser.add_argument("--column", default="auctionid")
    args: argparse.Namespace = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    counts: Counter[str] = Counter()
    total_rows = 0

    with open(output_path, "w", encoding="utf-8") as out:
        for row in iter_rows(input_path):
            raw_key = row.get(args.column, "")
            key = raw_key.strip()
            if not key:
                continue
            out.write(key + "\n")
            counts[key] += 1
            total_rows += 1

    manifest = {
        "dataset": "ebay",
        "input": str(input_path),
        "output": str(output_path),
        "column": args.column,
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
