"""Question logging for improving the semantic layer."""

from __future__ import annotations

import json
import os
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_LOG_PATH = ROOT / "logs" / "questions.jsonl"
DEFAULT_ENV_PATH = ROOT / ".env"
DEFAULT_SUPABASE_TABLE = "question_feedback"
_ENV_LOADED = False


@dataclass(frozen=True)
class QuestionLogEntry:
    timestamp_utc: str
    question: str
    ok: bool
    operation: str | None
    measure_id: str | None
    message: str
    parser: str | None = None
    dataset_id: str | None = None
    app_version: str | None = None


def log_question(
    question: str,
    ok: bool,
    operation: str | None,
    measure_id: str | None,
    message: str,
    parser: str | None = None,
    path: Path = DEFAULT_LOG_PATH,
) -> None:
    load_local_env()
    entry = QuestionLogEntry(
        timestamp_utc=datetime.now(UTC).isoformat(),
        question=question,
        ok=ok,
        operation=operation,
        measure_id=measure_id,
        message=message,
        parser=parser,
        dataset_id=os.getenv("DATASET_ID"),
        app_version=os.getenv("APP_VERSION"),
    )
    backend = feedback_backend()
    if backend == "off":
        return
    if backend == "supabase" and path == DEFAULT_LOG_PATH:
        try:
            log_question_supabase(entry)
            return
        except Exception:
            # Feedback should never break the reporting tool. Fall back to the
            # local log so failed hosted writes can still be reviewed.
            pass
    log_question_local(entry, path)


def feedback_backend() -> str:
    load_local_env()
    return os.getenv("FEEDBACK_BACKEND", "local").strip().lower()


def load_local_env(path: Path = DEFAULT_ENV_PATH) -> None:
    global _ENV_LOADED
    if _ENV_LOADED:
        return
    _ENV_LOADED = True
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def log_question_local(entry: QuestionLogEntry, path: Path = DEFAULT_LOG_PATH) -> None:
    path.parent.mkdir(exist_ok=True)
    with path.open("a") as f:
        f.write(json.dumps(asdict(entry), sort_keys=True) + "\n")


def supabase_config() -> tuple[str, str, str]:
    load_local_env()
    url = os.getenv("SUPABASE_URL", "").rstrip("/")
    key = os.getenv("SUPABASE_KEY", "")
    table = os.getenv("SUPABASE_FEEDBACK_TABLE", DEFAULT_SUPABASE_TABLE)
    if not url or not key:
        raise RuntimeError("SUPABASE_URL and SUPABASE_KEY are required for Supabase feedback.")
    return url, key, table


def supabase_headers(key: str) -> dict[str, str]:
    return {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }


def log_question_supabase(entry: QuestionLogEntry) -> None:
    url, key, table = supabase_config()
    request = Request(
        f"{url}/rest/v1/{table}",
        data=json.dumps(asdict(entry)).encode("utf-8"),
        headers={**supabase_headers(key), "Prefer": "return=minimal"},
        method="POST",
    )
    with urlopen(request, timeout=15):
        return


def read_question_log(path: Path = DEFAULT_LOG_PATH) -> list[QuestionLogEntry]:
    if feedback_backend() == "supabase" and path == DEFAULT_LOG_PATH:
        try:
            return read_question_log_supabase()
        except Exception:
            return read_question_log_local(path)
    return read_question_log_local(path)


def read_question_log_local(path: Path = DEFAULT_LOG_PATH) -> list[QuestionLogEntry]:
    if not path.exists():
        return []
    entries = []
    with path.open() as f:
        for line in f:
            if line.strip():
                entries.append(question_entry_from_dict(json.loads(line)))
    return entries


def read_question_log_supabase(limit: int = 1000) -> list[QuestionLogEntry]:
    url, key, table = supabase_config()
    params = urlencode(
        {
            "select": "timestamp_utc,question,ok,operation,measure_id,message,parser,dataset_id,app_version",
            "order": "timestamp_utc.asc",
            "limit": str(limit),
        }
    )
    request = Request(
        f"{url}/rest/v1/{table}?{params}",
        headers=supabase_headers(key),
        method="GET",
    )
    with urlopen(request, timeout=15) as response:
        payload = json.load(response)
    return [question_entry_from_dict(item) for item in payload]


def question_entry_from_dict(payload: dict) -> QuestionLogEntry:
    return QuestionLogEntry(
        timestamp_utc=payload["timestamp_utc"],
        question=payload["question"],
        ok=payload["ok"],
        operation=payload.get("operation"),
        measure_id=payload.get("measure_id"),
        message=payload.get("message", ""),
        parser=payload.get("parser"),
        dataset_id=payload.get("dataset_id"),
        app_version=payload.get("app_version"),
    )


def summarize_question_log(path: Path = DEFAULT_LOG_PATH) -> dict:
    entries = read_question_log(path)
    operations = Counter(entry.operation or "refused" for entry in entries)
    measures = Counter(entry.measure_id or "unknown" for entry in entries)
    parsers = Counter(entry.parser or "unknown" for entry in entries)
    refused = [entry for entry in entries if not entry.ok]
    return {
        "total_questions": len(entries),
        "accepted_questions": sum(1 for entry in entries if entry.ok),
        "refused_questions": len(refused),
        "operations": operations.most_common(),
        "measures": measures.most_common(),
        "parsers": parsers.most_common(),
        "recent_refusals": refused[-10:],
    }
