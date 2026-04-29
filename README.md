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

This repo starts with a small real CDC PLACES extract in `data/sample_places_county.csv` so the semantic layer and query behavior can be built before wiring in the full national download.

The sample table was fetched from the CDC PLACES county GIS-friendly 2025 release Socrata API on 2026-04-29. It is real PLACES data, but it is only a tiny subset of counties and measures.

Next steps:

- Expand the fetch script into a full CDC PLACES download/import command.
- Add a web UI for reporter-friendly querying.
- Add an LLM question parser that maps plain language to approved operations.
- Add tests for unsafe questions and caveat enforcement.
