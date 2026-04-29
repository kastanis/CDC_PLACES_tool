"""CLI for reporter-friendly PLACES queries."""

from pathlib import Path

import click

from cdc_places_tool.data import load_rows
from cdc_places_tool.feedback import feedback_backend, log_question, summarize_question_log, supabase_config
from cdc_places_tool.importer import fetch_county_data
from cdc_places_tool.query import compare, rank, summarize
from cdc_places_tool.render import (
    measure_to_text,
    print_compare_result,
    print_measure_explanation,
    print_measure_list,
    print_rank_result,
    print_summary_result,
    result_to_text,
)
from cdc_places_tool.router import route_question
from cdc_places_tool.semantic import load_semantic_layer
from cdc_places_tool.web import run_server


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
@click.option("--lowest", is_flag=True, help="Show the lowest values instead of highest")
@click.pass_context
def rank_cmd(ctx: click.Context, measure: str, state: str | None, limit: int, lowest: bool) -> None:
    """Rank places by a measure."""
    result = rank(ctx.obj["rows"], ctx.obj["layer"], measure, state=state, limit=limit, descending=not lowest)
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


@main.command("ask")
@click.option(
    "--parser",
    type=click.Choice(["rules", "ollama", "openai", "xai", "auto"]),
    default="rules",
    show_default=True,
    help="Question parser to use",
)
@click.argument("question")
@click.pass_context
def ask(ctx: click.Context, parser: str, question: str) -> None:
    """Route a plain-English question through approved operations."""
    answer = route_question(question, ctx.obj["rows"], ctx.obj["layer"], parser=parser)
    log_question(
        question=question,
        ok=answer.ok,
        operation=answer.operation,
        measure_id=answer.measure.id if answer.measure else None,
        message=answer.message,
    )
    if not answer.ok:
        click.echo(answer.message)
        raise click.Abort()
    if answer.operation == "explain" and answer.measure:
        click.echo(measure_to_text(ctx.obj["layer"], answer.measure))
        return
    if answer.result:
        click.echo(result_to_text(answer.result, ctx.obj["layer"]))


@main.command("fetch-counties")
def fetch_counties() -> None:
    """Fetch all county rows for the currently modeled semantic measures."""
    result = fetch_county_data()
    click.echo(f"Fetched {result.row_count} rows from {result.source_name}")
    click.echo(f"Wrote data: {result.output_path}")
    click.echo(f"Wrote metadata: {result.metadata_path}")


@main.command("serve")
@click.option("--host", default="127.0.0.1", show_default=True)
@click.option("--port", default=8765, show_default=True)
@click.pass_context
def serve(ctx: click.Context, host: str, port: int) -> None:
    """Start the local reporter-facing web UI."""
    run_server(ctx.obj["rows"], ctx.obj["layer"], host=host, port=port)


@main.command("feedback-summary")
def feedback_summary() -> None:
    """Summarize locally logged questions."""
    summary = summarize_question_log()
    click.echo(f"Total questions: {summary['total_questions']}")
    click.echo(f"Accepted: {summary['accepted_questions']}")
    click.echo(f"Refused: {summary['refused_questions']}")
    click.echo("\nOperations:")
    for operation, count in summary["operations"]:
        click.echo(f"- {operation}: {count}")
    click.echo("\nMeasures:")
    for measure, count in summary["measures"]:
        click.echo(f"- {measure}: {count}")
    if summary["recent_refusals"]:
        click.echo("\nRecent refusals:")
        for entry in summary["recent_refusals"]:
            click.echo(f"- {entry.question} -> {entry.message}")


@main.command("feedback-status")
def feedback_status() -> None:
    """Show which feedback backend is configured."""
    backend = feedback_backend()
    click.echo(f"Feedback backend: {backend}")
    if backend == "supabase":
        try:
            url, _, table = supabase_config()
        except RuntimeError as exc:
            click.echo(f"Supabase config: missing ({exc})")
            return
        click.echo(f"Supabase URL: {url}")
        click.echo(f"Supabase table: {table}")


@main.command("llm-status")
def llm_status() -> None:
    """Show local LLM parser configuration."""
    import os

    click.echo(f"Ollama URL: {os.getenv('OLLAMA_URL', 'http://localhost:11434')}")
    click.echo(f"Ollama model: {os.getenv('OLLAMA_MODEL', 'llama3.2')}")
    click.echo(f"OpenAI model: {os.getenv('OPENAI_MODEL', 'gpt-4o-mini')}")
    click.echo(f"OpenAI key configured: {'yes' if os.getenv('OPENAI_API_KEY') else 'no'}")
    click.echo(f"xAI model: {os.getenv('XAI_MODEL', 'grok-4.20')}")
    click.echo(f"xAI key configured: {'yes' if os.getenv('XAI_API_KEY') else 'no'}")


if __name__ == "__main__":
    main()
