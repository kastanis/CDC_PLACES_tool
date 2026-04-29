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

Ask with the optional local LLM parser:

```bash
places ask --parser ollama "Show me where insurance access looks worst in California"
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

Start the Streamlit app:

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

Summarize logged questions:

```bash
places feedback-summary
```

Check which feedback backend is configured:

```bash
places feedback-status
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

## Optional LLM Parser

The default parser is rule-based. You can optionally use a free local LLM through Ollama:

```bash
ollama pull llama3.2
ollama serve
places ask --parser ollama "Show me where insurance access looks worst in California"
```

The LLM only parses the question into structured intent. The semantic layer still validates measures, operations, units, and caveats before anything runs.

Use `--parser auto` to try Ollama first and fall back to rules if the local model is unavailable.

If you have hosted API keys, you can also use:

```bash
places ask --parser openai "Show me where insurance access looks worst in California"
places ask --parser xai "Show me where insurance access looks worst in California"
```

Those modes use API credits, so keep keys in `.env` or Streamlit secrets, never in Git.

## Feedback Loop

Plain-English questions are logged locally to `logs/questions.jsonl` by default, which is ignored by Git. The log records the question, whether it was answered, the matched operation, the matched measure, and any refusal message. It does not record names, emails, IP addresses, or browser identifiers.

For shared prototypes, set `FEEDBACK_BACKEND=supabase` and configure `SUPABASE_URL`, `SUPABASE_KEY`, and `SUPABASE_FEEDBACK_TABLE`. See [docs/supabase_feedback.md](docs/supabase_feedback.md).

For the hosted Streamlit version, see [docs/streamlit_deploy.md](docs/streamlit_deploy.md).

Use the log to decide what to add next: synonyms, measures, place aliases, new safe operations, or clearer refusal messages. The tool should not automatically expand acceptable questions without review.

See [docs/tool_pattern.md](docs/tool_pattern.md) for the reusable pattern behind this prototype.

Useful next steps:

- Add more PLACES measures to `semantic/measures.yaml`.
- Add an LLM parser as an optional layer on top of the deterministic router.
- Add a richer results page with charts and county profile views.
