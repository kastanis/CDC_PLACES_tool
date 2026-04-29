"""CLI for reporter-friendly PLACES queries."""

from pathlib import Path

import click

from cdc_places_tool.data import load_rows
from cdc_places_tool.query import compare, rank, summarize
from cdc_places_tool.render import (
    print_compare_result,
    print_measure_explanation,
    print_measure_list,
    print_rank_result,
    print_summary_result,
)
from cdc_places_tool.semantic import load_semantic_layer


@click.group()
@click.option("--data", "data_path", type=click.Path(path_type=Path), default=None)
@click.option("--semantic", "semantic_path", type=click.Path(path_type=Path), default=None)
@click.pass_context
def main(ctx: click.Context, data_path: Path | None, semantic_path: Path | None) -> None:
    """Query CDC PLACES-style data through approved semantic operations."""
    ctx.obj = {
        "rows": load_rows(data_path) if data_path else load_rows(),
        "layer": load_semantic_layer(semantic_path) if semantic_path else load_semantic_layer(),
    }


@main.command("list-measures")
@click.pass_context
def list_measures(ctx: click.Context) -> None:
    """List reporter-friendly measure names."""
    print_measure_list(ctx.obj["layer"])


@main.command("rank")
@click.option("--measure", "-m", required=True, help="Semantic measure ID, e.g. diabetes")
@click.option("--state", "-s", default=None, help="Optional state abbreviation")
@click.option("--limit", "-n", default=10, show_default=True, help="Number of rows")
@click.pass_context
def rank_cmd(ctx: click.Context, measure: str, state: str | None, limit: int) -> None:
    """Rank places by a measure."""
    result = rank(ctx.obj["rows"], ctx.obj["layer"], measure, state=state, limit=limit)
    print_rank_result(result, ctx.obj["layer"])


@main.command("compare")
@click.option("--measure", "-m", required=True, help="Semantic measure ID, e.g. uninsured")
@click.argument("places", nargs=-1, required=True)
@click.pass_context
def compare_cmd(ctx: click.Context, measure: str, places: tuple[str, ...]) -> None:
    """Compare named places for one measure."""
    result = compare(ctx.obj["rows"], ctx.obj["layer"], measure, list(places))
    print_compare_result(result, ctx.obj["layer"])


@main.command("summarize")
@click.option("--place", "-p", required=True, help='Place label, e.g. "Fresno County, CA"')
@click.pass_context
def summarize_cmd(ctx: click.Context, place: str) -> None:
    """Summarize the measures available for one place."""
    result = summarize(ctx.obj["rows"], ctx.obj["layer"], place)
    print_summary_result(result, ctx.obj["layer"])


@main.command()
@click.option("--measure", "-m", required=True, help="Semantic measure ID")
@click.pass_context
def explain(ctx: click.Context, measure: str) -> None:
    """Explain what a measure means and how to use it safely."""
    layer = ctx.obj["layer"]
    print_measure_explanation(layer, layer.get_measure(measure))


if __name__ == "__main__":
    main()
