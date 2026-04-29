# Supabase Feedback

The feedback loop can write question logs to Supabase instead of local JSONL.

Use this for shared prototypes where you want to review what people ask after deployment.

## 1. Create The Table

In Supabase, open the SQL editor and run:

```sql
create table if not exists public.question_feedback (
  id uuid primary key default gen_random_uuid(),
  created_at timestamptz not null default now(),
  timestamp_utc timestamptz not null,
  dataset_id text,
  app_version text,
  question text not null,
  ok boolean not null,
  operation text,
  measure_id text,
  message text
);

create index if not exists question_feedback_created_at_idx
  on public.question_feedback (created_at desc);

create index if not exists question_feedback_measure_idx
  on public.question_feedback (measure_id);

create index if not exists question_feedback_operation_idx
  on public.question_feedback (operation);
```

The same SQL lives in `supabase/schema.sql`.

## 2. Configure Environment Variables

For local development, copy `.env.example` to `.env` and set:

```text
FEEDBACK_BACKEND=supabase
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_KEY=your-server-side-supabase-key
SUPABASE_FEEDBACK_TABLE=question_feedback
DATASET_ID=cdc_places_county_gis_2025
APP_VERSION=local-dev
```

The CLI reads `.env` automatically. Existing shell environment variables take priority over values in `.env`.

For Streamlit Community Cloud, put those values in app secrets instead of committing them.

Do not expose a Supabase service role key in browser JavaScript or commit it to GitHub.

## 3. Check Status

```bash
places feedback-status
```

## 4. Review Questions

```bash
places feedback-summary
```

The summary reads from Supabase when `FEEDBACK_BACKEND=supabase`. If Supabase is unavailable, the tool falls back to the local JSONL log so feedback problems do not break the app.

## What To Review

- refused questions
- missing synonyms
- missing measures
- confusing place names
- requests for unsupported operations
- caveats that need clearer wording
