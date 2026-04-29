# Streamlit Deployment

This repo includes a Streamlit app:

```text
streamlit_app.py
```

## Run Locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run streamlit_app.py
```

Local feedback defaults to:

```text
logs/questions.jsonl
```

## Use Supabase Feedback

1. Create a Supabase project.
2. Run `supabase/schema.sql` in the Supabase SQL editor.
3. Add these secrets to Streamlit Community Cloud:

```toml
FEEDBACK_BACKEND = "supabase"
SUPABASE_URL = "https://your-project-ref.supabase.co"
SUPABASE_KEY = "your-server-side-supabase-key"
SUPABASE_FEEDBACK_TABLE = "question_feedback"
DATASET_ID = "cdc_places_county_gis_2025"
APP_VERSION = "streamlit"
```

Optional hosted parser secrets:

```toml
OPENAI_API_KEY = "your-openai-key"
OPENAI_MODEL = "gpt-4o-mini"
```

For local Streamlit development, copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml` and fill in the same values.

Do not commit `.streamlit/secrets.toml`.

## Deploy On Streamlit Community Cloud

Use:

```text
Repository: kastanis/CDC_PLACES_tool
Branch: main
Main file path: streamlit_app.py
```

Streamlit will install from `requirements.txt`.
