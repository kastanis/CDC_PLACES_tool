"""Fetch the real CDC PLACES county sample used by this repo."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = ROOT / "data" / "sample_places_county.csv"
ENDPOINT = "https://data.cdc.gov/resource/i46a-9kgh.json"

COUNTY_FIPS = [
    "06019",  # Fresno County, CA
    "06029",  # Kern County, CA
    "06037",  # Los Angeles County, CA
    "06075",  # San Francisco County, CA
    "12011",  # Broward County, FL
    "12057",  # Hillsborough County, FL
    "12086",  # Miami-Dade County, FL
    "12095",  # Orange County, FL
    "48029",  # Bexar County, TX
    "48113",  # Dallas County, TX
    "48201",  # Harris County, TX
    "48453",  # Travis County, TX
]

SOURCE_COLUMNS = [
    "stateabbr",
    "countyname",
    "countyfips",
    "totalpopulation",
    "diabetes_crudeprev",
    "obesity_crudeprev",
    "csmoking_crudeprev",
    "mhlth_crudeprev",
    "access2_crudeprev",
    "lpa_crudeprev",
    "checkup_crudeprev",
]

OUTPUT_COLUMNS = [
    "state",
    "county",
    "geoid",
    "population",
    "diabetes",
    "obesity",
    "smoking",
    "poor_mental_health",
    "uninsured",
    "physical_inactivity",
    "annual_checkup",
]


def build_url() -> str:
    quoted_fips = ",".join(f"'{fips}'" for fips in COUNTY_FIPS)
    params = urlencode(
        {
            "$select": ",".join(SOURCE_COLUMNS),
            "$where": f"countyfips in({quoted_fips})",
            "$order": "stateabbr,countyname",
        }
    )
    return f"{ENDPOINT}?{params}"


def county_label(county_name: str) -> str:
    if county_name.endswith("County"):
        return county_name
    return f"{county_name} County"


def fetch_rows() -> list[dict]:
    with urlopen(build_url(), timeout=30) as response:
        return json.load(response)


def transform_row(row: dict) -> dict:
    return {
        "state": row["stateabbr"],
        "county": county_label(row["countyname"]),
        "geoid": row["countyfips"],
        "population": row["totalpopulation"],
        "diabetes": row["diabetes_crudeprev"],
        "obesity": row["obesity_crudeprev"],
        "smoking": row["csmoking_crudeprev"],
        "poor_mental_health": row["mhlth_crudeprev"],
        "uninsured": row["access2_crudeprev"],
        "physical_inactivity": row["lpa_crudeprev"],
        "annual_checkup": row["checkup_crudeprev"],
    }


def main() -> None:
    rows = [transform_row(row) for row in fetch_rows()]
    with OUTPUT_PATH.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} rows to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
