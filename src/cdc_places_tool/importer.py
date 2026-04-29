"""Download CDC PLACES county data into the local reporter-friendly schema."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen


ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
DEFAULT_OUTPUT_PATH = DATA_DIR / "places_county_current.csv"
DEFAULT_METADATA_PATH = DATA_DIR / "places_county_current_metadata.json"
ENDPOINT = "https://data.cdc.gov/resource/i46a-9kgh.json"
METADATA_ENDPOINT = "https://data.cdc.gov/api/views/i46a-9kgh"

SOURCE_TO_LOCAL = {
    "stateabbr": "state",
    "countyname": "county",
    "countyfips": "geoid",
    "totalpopulation": "population",
    "diabetes_crudeprev": "diabetes",
    "obesity_crudeprev": "obesity",
    "csmoking_crudeprev": "smoking",
    "mhlth_crudeprev": "poor_mental_health",
    "access2_crudeprev": "uninsured",
    "lpa_crudeprev": "physical_inactivity",
    "checkup_crudeprev": "annual_checkup",
}


@dataclass(frozen=True)
class ImportResult:
    row_count: int
    output_path: Path
    metadata_path: Path
    source_name: str


def county_label(county_name: str) -> str:
    if county_name.endswith("County"):
        return county_name
    return f"{county_name} County"


def build_data_url(limit: int = 50000) -> str:
    params = urlencode(
        {
            "$select": ",".join(SOURCE_TO_LOCAL),
            "$limit": str(limit),
            "$order": "stateabbr,countyname",
        }
    )
    return f"{ENDPOINT}?{params}"


def fetch_json(url: str) -> object:
    with urlopen(url, timeout=60) as response:
        return json.load(response)


def transform_row(row: dict) -> dict:
    transformed = {}
    for source_column, local_column in SOURCE_TO_LOCAL.items():
        value = row.get(source_column, "")
        if source_column == "countyname" and value:
            value = county_label(value)
        transformed[local_column] = value
    return transformed


def fetch_county_data(
    output_path: Path = DEFAULT_OUTPUT_PATH,
    metadata_path: Path = DEFAULT_METADATA_PATH,
) -> ImportResult:
    DATA_DIR.mkdir(exist_ok=True)
    data_url = build_data_url()
    raw_rows = fetch_json(data_url)
    if not isinstance(raw_rows, list):
        raise ValueError("CDC PLACES API returned an unexpected data payload")

    rows = [transform_row(row) for row in raw_rows]
    fieldnames = list(SOURCE_TO_LOCAL.values())
    with output_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    metadata = fetch_json(METADATA_ENDPOINT)
    source_name = metadata.get("name", "CDC PLACES") if isinstance(metadata, dict) else "CDC PLACES"
    source_columns = [
        {"source_column": source, "local_column": local}
        for source, local in SOURCE_TO_LOCAL.items()
    ]
    metadata_payload = {
        "source_name": source_name,
        "source_endpoint": ENDPOINT,
        "metadata_endpoint": METADATA_ENDPOINT,
        "fetched_at_utc": datetime.now(UTC).isoformat(),
        "row_count": len(rows),
        "columns": source_columns,
        "notes": [
            "Values are modeled CDC PLACES prevalence estimates, not direct local counts.",
            "This import keeps only the measures currently defined in semantic/measures.yaml.",
        ],
    }
    metadata_path.write_text(json.dumps(metadata_payload, indent=2) + "\n")
    return ImportResult(len(rows), output_path, metadata_path, source_name)
