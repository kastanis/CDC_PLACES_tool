"""Guardrails for reporter-facing natural language questions."""

from __future__ import annotations


UNSUPPORTED_PATTERNS = {
    "causal": [
        "cause",
        "caused",
        "causes",
        "causing",
        "because of",
        "due to",
        "impact of",
        "effect of",
    ],
    "prediction": [
        "predict",
        "forecast",
        "next year",
        "future",
        "will happen",
    ],
    "counts": [
        "how many people",
        "number of people",
        "count of people",
        "residents have",
        "people have",
    ],
    "unsupported_analysis": [
        "correlation",
        "regression",
        "statistically significant",
        "p-value",
        "p value",
        "sql",
    ],
}

MESSAGES = {
    "causal": "I can compare and rank PLACES estimates, but I should not make causal claims from these modeled prevalence values alone.",
    "prediction": "I can summarize the current imported PLACES release, but I should not forecast future values from this dataset alone.",
    "counts": "I can answer prevalence questions. I should not convert percentages into people counts unless a specific, documented count method is added.",
    "unsupported_analysis": "That analysis is outside the approved semantic operations for this prototype.",
}


def check_question(question: str) -> tuple[bool, str | None]:
    normalized = question.lower()
    for category, patterns in UNSUPPORTED_PATTERNS.items():
        if any(pattern in normalized for pattern in patterns):
            return False, MESSAGES[category]
    return True, None
