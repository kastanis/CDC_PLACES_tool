"""Data loading helpers."""

from csv import DictReader
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATA_PATH = ROOT / "data" / "sample_places_county.csv"


def load_rows(path: Path = DEFAULT_DATA_PATH) -> list[dict]:
    with path.open(newline="") as f:
        rows = list(DictReader(f))
    for row in rows:
        for key, value in list(row.items()):
            if key in {"state", "county", "geoid"}:
                continue
            try:
                row[key] = float(value)
            except ValueError:
                pass
    return rows


def place_label(row: dict) -> str:
    return f"{row['county']}, {row['state']}"

