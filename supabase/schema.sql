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

-- For a server-side app, prefer keeping SUPABASE_KEY in Streamlit secrets or
-- local environment variables. Do not expose a service role key in browser JS.
