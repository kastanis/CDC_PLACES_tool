"""Optional local LLM parsing for plain-English questions."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from urllib.request import Request, urlopen

from cdc_places_tool.semantic import SemanticLayer


DEFAULT_OLLAMA_URL = "http://localhost:11434"
DEFAULT_OLLAMA_MODEL = "llama3.2"


@dataclass(frozen=True)
class ParsedIntent:
    operation: str | None
    measure_id: str | None
    state: str | None
    direction: str | None
    limit: int | None
    confidence: str | None = None


def parse_question_with_ollama(question: str, layer: SemanticLayer) -> ParsedIntent:
    url = os.getenv("OLLAMA_URL", DEFAULT_OLLAMA_URL).rstrip("/")
    model = os.getenv("OLLAMA_MODEL", DEFAULT_OLLAMA_MODEL)
    payload = {
        "model": model,
        "stream": False,
        "format": "json",
        "options": {"temperature": 0},
        "messages": [
            {"role": "system", "content": build_system_prompt(layer)},
            {"role": "user", "content": question},
        ],
    }
    request = Request(
        f"{url}/api/chat",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=float(os.getenv("OLLAMA_TIMEOUT", "20"))) as response:
        response_payload = json.load(response)
    content = response_payload.get("message", {}).get("content", "{}")
    return intent_from_json(content)


def build_system_prompt(layer: SemanticLayer) -> str:
    measures = [
        {
            "id": measure.id,
            "label": measure.label,
            "synonyms": measure.synonyms,
            "allowed_operations": measure.allowed_operations,
        }
        for measure in layer.measures.values()
    ]
    return (
        "You parse reporter questions about a county health dataset into JSON. "
        "You do not answer the question. Return only JSON with these keys: "
        "operation, measure_id, state, direction, limit, confidence. "
        "operation must be one of rank, compare, summarize, explain, unsupported. "
        "direction must be highest, lowest, or null. "
        "state must be a two-letter US postal abbreviation or null. "
        "measure_id must be one of the known measure ids or null. "
        "limit must be an integer or null. "
        "Known measures: "
        f"{json.dumps(measures)}"
    )


def intent_from_json(content: str) -> ParsedIntent:
    try:
        payload = json.loads(content)
    except json.JSONDecodeError:
        payload = {}
    return ParsedIntent(
        operation=clean_string(payload.get("operation")),
        measure_id=clean_string(payload.get("measure_id")),
        state=clean_state(payload.get("state")),
        direction=clean_string(payload.get("direction")),
        limit=clean_limit(payload.get("limit")),
        confidence=clean_string(payload.get("confidence")),
    )


def clean_string(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    value = value.strip()
    return value or None


def clean_state(value: object) -> str | None:
    value = clean_string(value)
    if not value:
        return None
    return value.upper()[:2]


def clean_limit(value: object) -> int | None:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return max(1, min(parsed, 25))
