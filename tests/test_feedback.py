import json

import cdc_places_tool.feedback as feedback
import streamlit_app
from cdc_places_tool.feedback import QuestionLogEntry, log_question, log_question_supabase, summarize_question_log


def test_logs_and_summarizes_questions(tmp_path):
    log_path = tmp_path / "questions.jsonl"
    log_question(
        question="Which counties have the highest diabetes rates?",
        ok=True,
        operation="rank",
        measure_id="diabetes",
        message="Highest diagnosed diabetes among adults values",
        parser="rules",
        path=log_path,
    )
    log_question(
        question="Did diabetes cause obesity?",
        ok=False,
        operation=None,
        measure_id=None,
        message="No causal claims.",
        path=log_path,
    )

    summary = summarize_question_log(log_path)
    assert summary["total_questions"] == 2
    assert summary["accepted_questions"] == 1
    assert summary["refused_questions"] == 1
    assert summary["operations"][0] == ("rank", 1)
    assert summary["parsers"][0] == ("rules", 1)


def test_writes_supabase_payload(monkeypatch):
    captured = {}

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["timeout"] = timeout
        captured["payload"] = json.loads(request.data.decode("utf-8"))
        captured["headers"] = dict(request.header_items())
        return FakeResponse()

    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setenv("SUPABASE_KEY", "test-key")
    monkeypatch.setenv("SUPABASE_FEEDBACK_TABLE", "question_feedback")
    monkeypatch.setattr("cdc_places_tool.feedback.urlopen", fake_urlopen)

    log_question_supabase(
        QuestionLogEntry(
            timestamp_utc="2026-04-29T00:00:00+00:00",
            question="Which counties have the highest diabetes rates?",
            ok=True,
            operation="rank",
            measure_id="diabetes",
            message="Highest values",
            parser="openai",
            dataset_id="test_dataset",
            app_version="test",
        )
    )

    assert captured["url"] == "https://example.supabase.co/rest/v1/question_feedback"
    assert captured["payload"]["measure_id"] == "diabetes"
    assert captured["payload"]["parser"] == "openai"
    assert captured["headers"]["Apikey"] == "test-key"


def test_loads_local_env_without_overriding_existing_values(tmp_path, monkeypatch):
    env_path = tmp_path / ".env"
    env_path.write_text("FEEDBACK_BACKEND=supabase\nAPP_VERSION=from-file\n")
    monkeypatch.delenv("FEEDBACK_BACKEND", raising=False)
    monkeypatch.setenv("APP_VERSION", "from-shell")
    monkeypatch.setattr(feedback, "_ENV_LOADED", False)

    feedback.load_local_env(env_path)

    assert feedback.feedback_backend() == "supabase"
    assert feedback.os.getenv("APP_VERSION") == "from-shell"


def test_streamlit_feedback_summary_handles_older_summary_shape(monkeypatch):
    calls = {"dataframes": []}

    monkeypatch.setattr(
        streamlit_app,
        "summarize_question_log",
        lambda: {
            "total_questions": 0,
            "accepted_questions": 0,
            "refused_questions": 0,
            "operations": [],
            "measures": [],
            "recent_refusals": [],
        },
    )
    monkeypatch.setattr(streamlit_app.st, "metric", lambda *args, **kwargs: None)
    monkeypatch.setattr(streamlit_app.st, "write", lambda *args, **kwargs: None)
    monkeypatch.setattr(streamlit_app.st, "dataframe", lambda rows, **kwargs: calls["dataframes"].append(rows))

    class FakeColumns:
        def metric(self, *args, **kwargs):
            return None

    monkeypatch.setattr(streamlit_app.st, "columns", lambda *args, **kwargs: [FakeColumns(), FakeColumns()])

    streamlit_app.render_feedback_summary()

    assert calls["dataframes"][-1] == []
