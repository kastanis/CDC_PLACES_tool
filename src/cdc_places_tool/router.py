"""Plain-English routing into approved semantic operations."""

from __future__ import annotations

import re
from dataclasses import dataclass

from cdc_places_tool.data import place_label
from cdc_places_tool.guardrails import check_question
from cdc_places_tool.query import compare, rank, summarize
from cdc_places_tool.semantic import Measure, SemanticLayer


STATE_NAMES = {
    "alabama": "AL",
    "alaska": "AK",
    "arizona": "AZ",
    "arkansas": "AR",
    "california": "CA",
    "colorado": "CO",
    "connecticut": "CT",
    "delaware": "DE",
    "district of columbia": "DC",
    "florida": "FL",
    "georgia": "GA",
    "hawaii": "HI",
    "idaho": "ID",
    "illinois": "IL",
    "indiana": "IN",
    "iowa": "IA",
    "kansas": "KS",
    "kentucky": "KY",
    "louisiana": "LA",
    "maine": "ME",
    "maryland": "MD",
    "massachusetts": "MA",
    "michigan": "MI",
    "minnesota": "MN",
    "mississippi": "MS",
    "missouri": "MO",
    "montana": "MT",
    "nebraska": "NE",
    "nevada": "NV",
    "new hampshire": "NH",
    "new jersey": "NJ",
    "new mexico": "NM",
    "new york": "NY",
    "north carolina": "NC",
    "north dakota": "ND",
    "ohio": "OH",
    "oklahoma": "OK",
    "oregon": "OR",
    "pennsylvania": "PA",
    "rhode island": "RI",
    "south carolina": "SC",
    "south dakota": "SD",
    "tennessee": "TN",
    "texas": "TX",
    "utah": "UT",
    "vermont": "VT",
    "virginia": "VA",
    "washington": "WA",
    "west virginia": "WV",
    "wisconsin": "WI",
    "wyoming": "WY",
}


@dataclass(frozen=True)
class RoutedAnswer:
    ok: bool
    message: str
    operation: str | None = None
    result: dict | None = None
    measure: Measure | None = None


def route_question(question: str, rows: list[dict], layer: SemanticLayer) -> RoutedAnswer:
    allowed, guardrail_message = check_question(question)
    if not allowed:
        return RoutedAnswer(ok=False, message=guardrail_message or "Unsupported question.")

    measure = find_measure(question, layer)
    places = find_places(question, rows)
    state = find_state(question)
    normalized = question.lower()

    try:
        if wants_explanation(normalized):
            if not measure:
                return RoutedAnswer(False, "I need a measure to explain. Try: explain uninsured.")
            return RoutedAnswer(True, f"Explaining {measure.label}.", "explain", measure=measure)

        if wants_summary(normalized):
            if places:
                result = summarize(rows, layer, places[0])
                return RoutedAnswer(True, result["headline"], "summarize", result, measure)
            return RoutedAnswer(False, "I need a place to summarize. Try: summarize Fresno County, CA.")

        if wants_comparison(normalized) or len(places) >= 2:
            if not measure:
                return RoutedAnswer(False, "I need a measure for the comparison.")
            if len(places) < 2:
                return RoutedAnswer(False, "I need at least two places to compare.")
            result = compare(rows, layer, measure.id, places)
            return RoutedAnswer(True, result["headline"], "compare", result, measure)

        if wants_ranking(normalized) or measure:
            if not measure:
                return RoutedAnswer(False, "I need a measure to rank.")
            limit = find_limit(question)
            result = rank(rows, layer, measure.id, state=state, limit=limit, descending=not wants_lowest(normalized))
            return RoutedAnswer(True, result["headline"], "rank", result, measure)
    except (KeyError, ValueError) as exc:
        return RoutedAnswer(False, str(exc))

    return RoutedAnswer(
        False,
        "I can rank, compare, summarize a place, or explain a measure. Try asking: Which California counties have the highest uninsured rates?",
    )


def find_measure(question: str, layer: SemanticLayer) -> Measure | None:
    normalized = question.lower()
    candidates: list[tuple[int, Measure]] = []
    for measure in layer.measures.values():
        terms = [measure.id.replace("_", " "), measure.label, *measure.synonyms]
        for term in terms:
            term_norm = term.lower()
            if term_norm and term_norm in normalized:
                candidates.append((len(term_norm), measure))
    if not candidates:
        return None
    return sorted(candidates, key=lambda item: item[0], reverse=True)[0][1]


def find_places(question: str, rows: list[dict]) -> list[str]:
    normalized = normalize_text(question)
    matches = []
    for row in rows:
        label = place_label(row)
        county = row["county"]
        label_norm = normalize_text(label)
        county_norm = normalize_text(county)
        if label_norm in normalized or county_norm in normalized:
            matches.append(label)
    return sorted(set(matches))


def find_state(question: str) -> str | None:
    normalized = question.lower()
    for name, abbr in STATE_NAMES.items():
        if name in normalized:
            return abbr
    tokens = {token.strip(".,?!():;").upper() for token in question.split()}
    for abbr in STATE_NAMES.values():
        if abbr in tokens:
            return abbr
    return None


def find_limit(question: str) -> int:
    match = re.search(r"\btop\s+(\d{1,2})\b", question.lower())
    if not match:
        return 10
    return max(1, min(int(match.group(1)), 25))


def wants_ranking(normalized: str) -> bool:
    return any(term in normalized for term in ["highest", "lowest", "rank", "top", "worst", "best"])


def wants_lowest(normalized: str) -> bool:
    return any(term in normalized for term in ["lowest", "least", "bottom"])


def wants_comparison(normalized: str) -> bool:
    return any(term in normalized for term in ["compare", "versus", " vs ", "difference between"])


def wants_summary(normalized: str) -> bool:
    return any(term in normalized for term in ["summarize", "what stands out", "profile", "overview"])


def wants_explanation(normalized: str) -> bool:
    return normalized.startswith("explain") or "what does" in normalized or "what is" in normalized


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value.lower().replace("-", " ")).strip()
