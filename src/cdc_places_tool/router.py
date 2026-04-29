"""Plain-English routing into approved semantic operations."""

from __future__ import annotations

import re
from dataclasses import dataclass

from cdc_places_tool.data import place_label
from cdc_places_tool.guardrails import check_question
from cdc_places_tool.llm_parser import (
    ParsedIntent,
    parse_question_with_ollama,
    parse_question_with_openai,
)
from cdc_places_tool.query import compare, rank, summarize
from cdc_places_tool.semantic import Measure, SemanticLayer, normalize_term


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
    parser: str | None = None


def route_question(
    question: str,
    rows: list[dict],
    layer: SemanticLayer,
    parser: str = "rules",
) -> RoutedAnswer:
    allowed, guardrail_message = check_question(question)
    if not allowed:
        return RoutedAnswer(ok=False, message=guardrail_message or "Unsupported question.", parser=parser)

    if parser in {"ollama", "openai", "auto"}:
        try:
            intent = parse_question_with_provider(question, layer, parser)
            parser_used = "ollama" if parser == "auto" else parser
            return route_intent(question, rows, layer, intent, parser_used=parser_used)
        except Exception as exc:
            if parser != "auto":
                return RoutedAnswer(
                    ok=False,
                    message=f"{parser} parser unavailable or misconfigured: {exc}",
                    parser=parser,
                )
            parser = "rules"

    measure = find_measure(question, layer)
    places = find_places(question, rows)
    state = find_state(question)
    normalized = question.lower()

    try:
        if wants_explanation(normalized):
            if not measure:
                return RoutedAnswer(False, "I need a measure to explain. Try: explain uninsured.", parser=parser)
            return RoutedAnswer(True, f"Explaining {measure.label}.", "explain", measure=measure, parser=parser)

        if wants_summary(normalized):
            if places:
                result = summarize(rows, layer, places[0])
                return RoutedAnswer(True, result["headline"], "summarize", result, measure, parser=parser)
            return RoutedAnswer(False, "I need a place to summarize. Try: summarize Fresno County, CA.", parser=parser)

        if wants_comparison(normalized) or len(places) >= 2:
            if not measure:
                return RoutedAnswer(False, "I need a measure for the comparison.", parser=parser)
            if len(places) < 2:
                return RoutedAnswer(False, "I need at least two places to compare.", parser=parser)
            result = compare(rows, layer, measure.id, places)
            return RoutedAnswer(True, result["headline"], "compare", result, measure, parser=parser)

        if wants_ranking(normalized) or measure:
            if not measure:
                return RoutedAnswer(False, "I need a measure to rank.", parser=parser)
            limit = find_limit(question)
            result = rank(rows, layer, measure.id, state=state, limit=limit, descending=not wants_lowest(normalized))
            return RoutedAnswer(True, result["headline"], "rank", result, measure, parser=parser)
    except (KeyError, ValueError) as exc:
        return RoutedAnswer(False, str(exc), parser=parser)

    return RoutedAnswer(
        False,
        "I can rank, compare, summarize a place, or explain a measure. Try asking: Which California counties have the highest uninsured rates?",
        parser=parser,
    )


def parse_question_with_provider(question: str, layer: SemanticLayer, parser: str) -> ParsedIntent:
    if parser == "openai":
        return parse_question_with_openai(question, layer)
    return parse_question_with_ollama(question, layer)


def route_intent(
    question: str,
    rows: list[dict],
    layer: SemanticLayer,
    intent: ParsedIntent,
    parser_used: str | None = None,
) -> RoutedAnswer:
    operation = intent.operation
    if operation == "unsupported" or operation is None:
        return route_question(question, rows, layer, parser="rules")

    measure = None
    if intent.measure_id:
        try:
            measure = layer.get_measure(intent.measure_id)
        except KeyError:
            measure = find_measure(question, layer)
    else:
        measure = find_measure(question, layer)

    places = find_places(question, rows)
    state = intent.state if intent.state in available_states(rows) else find_state(question)

    try:
        if operation == "explain":
            if not measure:
                return RoutedAnswer(False, "I need a measure to explain. Try: explain uninsured.", parser=parser_used)
            return RoutedAnswer(True, f"Explaining {measure.label}.", "explain", measure=measure, parser=parser_used)

        if operation == "summarize":
            if places:
                result = summarize(rows, layer, places[0])
                return RoutedAnswer(True, result["headline"], "summarize", result, measure, parser=parser_used)
            return RoutedAnswer(False, "I need a place to summarize. Try: summarize Fresno County, CA.", parser=parser_used)

        if operation == "compare":
            if not measure:
                return RoutedAnswer(False, "I need a measure for the comparison.", parser=parser_used)
            if len(places) < 2:
                return RoutedAnswer(False, "I need at least two places to compare.", parser=parser_used)
            result = compare(rows, layer, measure.id, places)
            return RoutedAnswer(True, result["headline"], "compare", result, measure, parser=parser_used)

        if operation == "rank":
            if not measure:
                return RoutedAnswer(False, "I need a measure to rank.", parser=parser_used)
            limit = intent.limit or find_limit(question)
            descending = intent.direction != "lowest"
            result = rank(rows, layer, measure.id, state=state, limit=limit, descending=descending)
            if not result["rows"]:
                state_label = f" for {state}" if state else ""
                return RoutedAnswer(False, f"No rows found for {measure.label}{state_label}.", parser=parser_used)
            return RoutedAnswer(True, result["headline"], "rank", result, measure, parser=parser_used)
    except (KeyError, ValueError) as exc:
        return RoutedAnswer(False, str(exc), parser=parser_used)

    return route_question(question, rows, layer, parser="rules")


def find_measure(question: str, layer: SemanticLayer) -> Measure | None:
    normalized = normalize_term(question)
    candidates: list[tuple[int, Measure]] = []
    for measure in layer.measures.values():
        terms = [measure.id, measure.label, *measure.synonyms]
        for term in terms:
            term_norm = normalize_term(term)
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


def available_states(rows: list[dict]) -> set[str]:
    return {str(row.get("state", "")).upper() for row in rows if row.get("state")}


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
    return normalize_term(value)
