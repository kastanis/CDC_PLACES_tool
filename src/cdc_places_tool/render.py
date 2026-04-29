"""Reporter-friendly output rendering."""

from rich.console import Console
from rich.table import Table

from cdc_places_tool.data import place_label
from cdc_places_tool.semantic import Measure, SemanticLayer


console = Console()


def print_measure_list(layer: SemanticLayer) -> None:
    table = Table(title="Available Measures")
    table.add_column("ID", style="bold")
    table.add_column("Label")
    table.add_column("Universe")
    for measure in layer.measures.values():
        table.add_row(measure.id, measure.label, measure.universe)
    console.print(table)


def print_rank_result(result: dict, layer: SemanticLayer) -> None:
    measure: Measure = result["measure"]
    table = Table(title=result["headline"])
    table.add_column("Rank", justify="right")
    table.add_column("Place")
    table.add_column(measure.label, justify="right")
    for index, row in enumerate(result["rows"], start=1):
        table.add_row(str(index), place_label(row), format_value(row[measure.column], measure))
    console.print(table)
    print_cautions(layer, measure)


def print_compare_result(result: dict, layer: SemanticLayer) -> None:
    measure: Measure = result["measure"]
    table = Table(title=result["headline"])
    table.add_column("Place")
    table.add_column(measure.label, justify="right")
    for row in result["rows"]:
        table.add_row(place_label(row), format_value(row[measure.column], measure))
    console.print(table)
    print_cautions(layer, measure)


def print_summary_result(result: dict, layer: SemanticLayer) -> None:
    row = result["place"]
    table = Table(title=result["headline"])
    table.add_column("Measure")
    table.add_column("Estimate", justify="right")
    table.add_column("Universe")
    for measure, value in result["values"]:
        table.add_row(measure.label, format_value(value, measure), measure.universe)
    console.print(table)
    console.print("[bold]Reporter note:[/bold] Use this as a lead-finding view. Follow up with local sources and context.")
    print_cautions(layer, None)


def print_measure_explanation(layer: SemanticLayer, measure: Measure) -> None:
    console.print(f"[bold]{measure.label}[/bold]")
    console.print(measure.plain_language)
    console.print(f"Unit: {measure.unit}")
    console.print(f"Universe: {measure.universe}")
    print_cautions(layer, measure)


def print_cautions(layer: SemanticLayer, measure: Measure | None) -> None:
    caveats = list(layer.default_caveats)
    if measure:
        caveats.extend(measure.caveats)
    console.print("\n[bold]Cautions[/bold]")
    for caveat in caveats:
        console.print(f"- {caveat}")


def format_value(value: float | None, measure: Measure) -> str:
    if value is None:
        return "Not available"
    if measure.unit == "percent":
        return f"{value:.1f}%"
    return f"{value:g} {measure.unit}"


def result_to_text(result: dict, layer: SemanticLayer) -> str:
    operation = result["operation"]
    if operation == "rank":
        return rank_to_text(result, layer)
    if operation == "compare":
        return compare_to_text(result, layer)
    if operation == "summarize":
        return summary_to_text(result, layer)
    return "Unsupported result."


def rank_to_text(result: dict, layer: SemanticLayer) -> str:
    measure: Measure = result["measure"]
    lines = [result["headline"]]
    for index, row in enumerate(result["rows"], start=1):
        lines.append(f"{index}. {place_label(row)}: {format_value(row[measure.column], measure)}")
    lines.extend(caution_lines(layer, measure))
    return "\n".join(lines)


def compare_to_text(result: dict, layer: SemanticLayer) -> str:
    measure: Measure = result["measure"]
    lines = [result["headline"]]
    for row in result["rows"]:
        lines.append(f"- {place_label(row)}: {format_value(row[measure.column], measure)}")
    lines.extend(caution_lines(layer, measure))
    return "\n".join(lines)


def summary_to_text(result: dict, layer: SemanticLayer) -> str:
    lines = [result["headline"]]
    for measure, value in result["values"]:
        lines.append(f"- {measure.label}: {format_value(value, measure)}")
    lines.append("Reporter note: Use this as a lead-finding view. Follow up with local sources and context.")
    lines.extend(caution_lines(layer, None))
    return "\n".join(lines)


def measure_to_text(layer: SemanticLayer, measure: Measure) -> str:
    lines = [
        measure.label,
        measure.plain_language,
        f"Unit: {measure.unit}",
        f"Universe: {measure.universe}",
    ]
    lines.extend(caution_lines(layer, measure))
    return "\n".join(lines)


def caution_lines(layer: SemanticLayer, measure: Measure | None) -> list[str]:
    caveats = list(layer.default_caveats)
    if measure:
        caveats.extend(measure.caveats)
    return ["", "Cautions", *[f"- {caveat}" for caveat in caveats]]
