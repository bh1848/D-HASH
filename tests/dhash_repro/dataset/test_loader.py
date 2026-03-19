import zipfile
from pathlib import Path

import pytest

from dhash_repro.dataset.loader import load_csv_dataset, load_logs_dataset


def _write_zip(zip_path: Path, files: dict[str, str]) -> None:
    with zipfile.ZipFile(zip_path, "w") as zf:
        for name, content in files.items():
            zf.writestr(name, content)


def test_load_logs_dataset_prefers_access_log_inside_zip(tmp_path: Path) -> None:
    zip_path = tmp_path / "nasa.zip"
    _write_zip(
        zip_path,
        {
            "notes.txt": "ignore me\n",
            "access.log": (
                "host - - [01/Aug/1995:00:00:01 -0400] " '"GET /index.html HTTP/1.0" 200 123\n'
            ),
        },
    )

    keys, _meta = load_logs_dataset(str(zip_path))

    assert keys == ["/index.html"]


def test_load_csv_dataset_prefers_auction_csv_inside_zip(tmp_path: Path) -> None:
    zip_path = tmp_path / "ebay.zip"
    _write_zip(
        zip_path,
        {
            "misc.csv": "other,field\nx,y\n",
            "auction.csv": "auctionid,bid\nA1,10\nA2,20\nA1,30\n",
        },
    )

    keys, _meta = load_csv_dataset(str(zip_path))

    assert keys == ["A1", "A2"]


def test_load_csv_dataset_raises_for_ambiguous_zip_csv_candidates(tmp_path: Path) -> None:
    zip_path = tmp_path / "ambiguous.zip"
    _write_zip(
        zip_path,
        {
            "first.csv": "auctionid,bid\nA1,10\n",
            "second.csv": "auctionid,bid\nA2,20\n",
        },
    )

    with pytest.raises(ValueError, match="Multiple CSV candidates found inside zip"):
        load_csv_dataset(str(zip_path))
