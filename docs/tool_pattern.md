# Dataset Tool Pattern

This repo is a prototype pattern for spinning up a reporter-facing tool around a structured dataset.

The goal is not to let people ask anything. The goal is to make the useful questions easy, keep answers grounded in the data, and make unsupported questions visible so the tool can improve.

## The Pattern

1. Import the data.
2. Normalize it into a simple local table.
3. Define a semantic layer.
4. Expose a small set of approved query operations.
5. Route plain-English questions into those operations.
6. Refuse questions the data cannot safely answer.
7. Log questions so the team can improve coverage.

## What Changes For A New Dataset

Dataset-specific pieces:

- `src/cdc_places_tool/importer.py`
- `semantic/measures.yaml`
- source metadata in `data/`
- dataset-specific caveats
- any new approved operations

Reusable pieces:

- semantic layer loading
- rank/compare/summarize/explain query pattern
- plain-English router structure
- guardrail structure
- local web UI structure
- feedback logging

## Semantic Layer Checklist

Every measure should define:

- stable ID
- reporter-friendly label
- source column
- unit
- universe
- plain-language definition
- synonyms people may type
- allowed operations
- caveats

This is what keeps a plain-English interface from becoming an ungrounded chat box.

## Feedback Loop

The tool logs questions locally to:

```text
logs/questions.jsonl
```

For shared deployments, the same feedback interface can write to Supabase by setting:

```text
FEEDBACK_BACKEND=supabase
```

Each row includes:

- timestamp
- question
- whether the tool answered
- operation
- measure ID
- message or refusal reason

Use this to review:

- common refused questions
- missing synonyms
- missing measures
- places people type differently than the data
- operations reporters keep asking for
- caveats that need clearer wording

Run:

```bash
places feedback-summary
```

The feedback loop should not automatically make new questions acceptable. A person should review the logs, decide whether the dataset can safely support the request, then update the semantic layer, router, tests, and caveats.

## Launch Checklist

Before sharing a dataset tool:

- Confirm source and fetch date are documented.
- Confirm row counts match the source.
- Confirm every visible measure has a definition and caveat.
- Confirm unsupported questions are refused.
- Confirm question logging is disclosed to users.
- Confirm logs do not collect names, emails, IP addresses, or sensitive text.
- Add tests for the highest-risk questions.

## Good First Improvements

- Add more synonyms from actual question logs.
- Add a place-name alias file.
- Add charts for rank and compare views.
- Add export buttons for results.
- Add a review queue for refused questions.
