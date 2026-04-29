# CDC PLACES Tool

A reporter-first prototype for querying CDC PLACES-style local health data through a semantic layer.

The goal is not to expose a blank SQL box. The goal is to let reporters ask useful questions while the semantic layer keeps units, caveats, geography, and safe language attached to the answer.

## Why PLACES

CDC PLACES is a strong first dataset for this idea because the measures are intuitive, the geographies are familiar, and the caveats are important but explainable. Reporters can ask questions like:

- Which counties have the highest diabetes prevalence?
- Compare smoking, obesity, and uninsured rates in these counties.
- What stands out in Fresno County?
- What should I be careful about before reporting this?

## Install

```bash
cd /Users/akastanis/Git_work/CDC_PLACES_tool
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Try It

List available measures:

```bash
places list-measures
```

Rank counties:

```bash
places rank --measure diabetes --state CA --limit 5
```

Compare counties:

```bash
places compare --measure poor_mental_health --places "Fresno County, CA" "Los Angeles County, CA"
```

Summarize a place:

```bash
places summarize --place "Fresno County, CA"
```

Explain a measure:

```bash
places explain --measure uninsured
```

## Current Status

This repo starts with a small sample table in `data/sample_places_county.csv` so the semantic layer and query behavior can be built before wiring in the full CDC download.

The sample table is development/demo data only. Do not use it for reporting.

Next steps:

- Add a real CDC PLACES download/import command.
- Add a web UI for reporter-friendly querying.
- Add an LLM question parser that maps plain language to approved operations.
- Add tests for unsafe questions and caveat enforcement.
