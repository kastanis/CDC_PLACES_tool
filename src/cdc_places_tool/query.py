"""Approved query operations over PLACES-style rows."""

from cdc_places_tool.data import place_label
from cdc_places_tool.semantic import Measure, SemanticLayer


def has_numeric_value(row: dict, column: str) -> bool:
    return isinstance(row.get(column), int | float)


def rank(
    rows: list[dict],
    layer: SemanticLayer,
    measure_id: str,
    state: str | None = None,
    limit: int = 10,
    descending: bool = True,
) -> dict:
    measure = layer.get_measure(measure_id)
    filtered = [row for row in rows if state is None or row["state"].lower() == state.lower()]
    filtered = [row for row in filtered if has_numeric_value(row, measure.column)]
    ranked = sorted(filtered, key=lambda row: row[measure.column], reverse=descending)[:limit]
    direction = "Highest" if descending else "Lowest"
    return {
        "operation": "rank",
        "measure": measure,
        "rows": ranked,
        "headline": f"{direction} {measure.label.lower()} values",
    }


def compare(rows: list[dict], layer: SemanticLayer, measure_id: str, places: list[str]) -> dict:
    measure = layer.get_measure(measure_id)
    wanted = {place.lower() for place in places}
    matched = [row for row in rows if place_label(row).lower() in wanted and has_numeric_value(row, measure.column)]
    return {
        "operation": "compare",
        "measure": measure,
        "rows": sorted(matched, key=lambda row: row[measure.column], reverse=True),
        "headline": f"Comparison for {measure.label.lower()}",
    }


def summarize(rows: list[dict], layer: SemanticLayer, place: str) -> dict:
    wanted = place.lower()
    matches = [row for row in rows if place_label(row).lower() == wanted]
    if not matches:
        raise ValueError(f"Place not found: {place}")
    row = matches[0]
    values = []
    for measure in layer.measures.values():
        if not has_numeric_value(row, measure.column):
            continue
        values.append((measure, row[measure.column]))
    values.sort(key=lambda item: item[1], reverse=True)
    return {
        "operation": "summarize",
        "place": row,
        "values": values,
        "headline": f"What stands out in {place_label(row)}",
    }
