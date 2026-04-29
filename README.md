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

Rank lowest values:

```bash
places rank --measure diabetes --state CA --limit 5 --lowest
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

Ask a plain-English question:

```bash
places ask "Which California counties have the highest uninsured rates?"
```

Fetch the current county data for the modeled semantic measures:

```bash
places fetch-counties
```

Start the local reporter-facing web UI:

```bash
places serve
```

Then open:

```text
http://127.0.0.1:8765
```

## Current Status

This repo starts with a small real CDC PLACES extract in `data/sample_places_county.csv` and can now fetch a full county file for the currently modeled semantic measures into `data/places_county_current.csv`.

The sample table was fetched from the CDC PLACES county GIS-friendly 2025 release Socrata API on 2026-04-29. It is real PLACES data, but it is only a tiny subset of counties and measures.

## Guardrails

The plain-English router only maps questions into approved semantic operations:

- `rank`
- `compare`
- `summarize`
- `explain`

It refuses questions that ask for causal claims, forecasts, arbitrary statistical modeling, SQL, or people counts derived from prevalence estimates.

Useful next steps:

- Add more PLACES measures to `semantic/measures.yaml`.
- Add an LLM parser as an optional layer on top of the deterministic router.
- Add a richer results page with charts and county profile views.
