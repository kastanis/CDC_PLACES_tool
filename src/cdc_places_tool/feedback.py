"""Local question logging for improving the semantic layer."""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_LOG_PATH = ROOT / "logs" / "questions.jsonl"


@dataclass(frozen=True)
class QuestionLogEntry:
    timestamp_utc: str
    question: str
    ok: bool
    operation: str | None
    measure_id: str | None
    message: str


def log_question(
    question: str,
    ok: bool,
    operation: str | None,
    measure_id: str | None,
    message: str,
    path: Path = DEFAULT_LOG_PATH,
) -> None:
    path.parent.mkdir(exist_ok=True)
    entry = QuestionLogEntry(
        timestamp_utc=datetime.now(UTC).isoformat(),
        question=question,
        ok=ok,
        operation=operation,
        measure_id=measure_id,
        message=message,
    )
    with path.open("a") as f:
        f.write(json.dumps(asdict(entry), sort_keys=True) + "\n")


def read_question_log(path: Path = DEFAULT_LOG_PATH) -> list[QuestionLogEntry]:
    if not path.exists():
        return []
    entries = []
    with path.open() as f:
        for line in f:
            if line.strip():
                entries.append(QuestionLogEntry(**json.loads(line)))
    return entries


def summarize_question_log(path: Path = DEFAULT_LOG_PATH) -> dict:
    entries = read_question_log(path)
    operations = Counter(entry.operation or "refused" for entry in entries)
    measures = Counter(entry.measure_id or "unknown" for entry in entries)
    refused = [entry for entry in entries if not entry.ok]
    return {
        "total_questions": len(entries),
        "accepted_questions": sum(1 for entry in entries if entry.ok),
        "refused_questions": len(refused),
        "operations": operations.most_common(),
        "measures": measures.most_common(),
        "recent_refusals": refused[-10:],
    }
