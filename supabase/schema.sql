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
  parser text,
  message text
);

alter table public.question_feedback
  add column if not exists parser text;

create index if not exists question_feedback_created_at_idx
  on public.question_feedback (created_at desc);

create index if not exists question_feedback_measure_idx
  on public.question_feedback (measure_id);

create index if not exists question_feedback_operation_idx
  on public.question_feedback (operation);

create index if not exists question_feedback_parser_idx
  on public.question_feedback (parser);

alter table public.question_feedback enable row level security;

grant insert on public.question_feedback to anon;
grant insert on public.question_feedback to authenticated;

drop policy if exists "Allow public feedback inserts" on public.question_feedback;
create policy "Allow public feedback inserts"
  on public.question_feedback
  for insert
  to anon, authenticated
  with check (true);

-- For a server-side app, prefer keeping SUPABASE_KEY in Streamlit secrets or
-- local environment variables. Do not expose a service role key in browser JS.
