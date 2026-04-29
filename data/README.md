# Data Notes

`sample_places_county.csv` is a small real extract from CDC PLACES County Data (GIS Friendly Format), 2025 release.

`places_county_current.csv` is the full county-level import for the measures currently modeled in `semantic/measures.yaml`. The app uses this full file by default when it is present, and falls back to the sample file only if the full import has not been fetched.

Source endpoint:

```text
https://data.cdc.gov/resource/i46a-9kgh.json
```

Fetched on: 2026-04-29

The file keeps a reporter-friendly schema for the prototype:

| Local column | CDC source column |
| --- | --- |
| `state` | `stateabbr` |
| `county` | `countyname` with ` County` appended for these county samples |
| `geoid` | `countyfips` |
| `population` | `totalpopulation` |
| `diabetes` | `diabetes_crudeprev` |
| `obesity` | `obesity_crudeprev` |
| `smoking` | `csmoking_crudeprev` |
| `poor_mental_health` | `mhlth_crudeprev` |
| `uninsured` | `access2_crudeprev` |
| `physical_inactivity` | `lpa_crudeprev` |
| `annual_checkup` | `checkup_crudeprev` |

These are modeled prevalence estimates. The sample is useful for building and testing the semantic layer, but it is not a substitute for the full PLACES dataset.

Run this command to fetch all county rows for the currently modeled semantic measures:

```bash
places fetch-counties
```

That command writes:

- `data/places_county_current.csv`
- `data/places_county_current_metadata.json`
