"""Streamlit app for the CDC PLACES reporter tool."""

from __future__ import annotations

import os
import sys
from collections import Counter
from pathlib import Path

import streamlit as st


ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from cdc_places_tool.data import load_rows, place_label
from cdc_places_tool.feedback import feedback_backend, log_question, summarize_question_log
from cdc_places_tool.query import compare, rank, summarize
from cdc_places_tool.render import format_value, measure_to_text, result_to_text
from cdc_places_tool.router import route_question
from cdc_places_tool.semantic import Measure, load_semantic_layer


def load_streamlit_secrets() -> None:
    try:
        secrets = st.secrets
        _ = secrets.keys()
    except Exception:
        return
    for key in [
        "FEEDBACK_BACKEND",
        "SUPABASE_URL",
        "SUPABASE_KEY",
        "SUPABASE_FEEDBACK_TABLE",
        "DATASET_ID",
        "APP_VERSION",
        "OPENAI_API_KEY",
        "OPENAI_MODEL",
        "OPENAI_TIMEOUT",
    ]:
        try:
            value = secrets[key]
        except KeyError:
            continue
        os.environ.setdefault(key, str(value))


@st.cache_data(show_spinner=False)
def cached_rows() -> list[dict]:
    return load_rows()


@st.cache_resource(show_spinner=False)
def cached_layer():
    return load_semantic_layer()


def log_routed_question(question: str, answer) -> None:
    log_question(
        question=question,
        ok=answer.ok,
        operation=answer.operation,
        measure_id=answer.measure.id if answer.measure else None,
        message=answer.message,
        parser=answer.parser,
    )


def render_text_answer(text: str) -> None:
    st.code(text, language=None)


def render_rank_table(result: dict) -> None:
    measure: Measure = result["measure"]
    rows = [
        {
            "Rank": index,
            "Place": place_label(row),
            measure.label: format_value(row[measure.column], measure),
        }
        for index, row in enumerate(result["rows"], start=1)
    ]
    st.subheader(result["headline"])
    st.dataframe(rows, hide_index=True, width="stretch")


def render_compare_table(result: dict) -> None:
    measure: Measure = result["measure"]
    rows = [
        {
            "Place": place_label(row),
            measure.label: format_value(row[measure.column], measure),
        }
        for row in result["rows"]
    ]
    st.subheader(result["headline"])
    st.dataframe(rows, hide_index=True, width="stretch")


def render_summary_table(result: dict) -> None:
    rows = [
        {
            "Measure": measure.label,
            "Estimate": format_value(value, measure),
            "Universe": measure.universe,
        }
        for measure, value in result["values"]
    ]
    st.subheader(result["headline"])
    st.dataframe(rows, hide_index=True, width="stretch")


def render_cautions(layer, measure: Measure | None = None) -> None:
    caveats = list(layer.default_caveats)
    if measure:
        caveats.extend(measure.caveats)
    with st.expander("Cautions and source notes", expanded=True):
        for caveat in caveats:
            st.write(f"- {caveat}")


def render_feedback_summary() -> None:
    summary = summarize_question_log()
    parsers = summary.get("parsers", [])
    st.metric("Questions", summary["total_questions"])
    cols = st.columns(2)
    cols[0].metric("Accepted", summary["accepted_questions"])
    cols[1].metric("Refused", summary["refused_questions"])

    st.write("Operations")
    st.dataframe(
        [{"Operation": operation, "Count": count} for operation, count in summary["operations"]],
        hide_index=True,
        width="stretch",
    )

    st.write("Parsers")
    st.dataframe(
        [{"Parser": parser, "Count": count} for parser, count in parsers],
        hide_index=True,
        width="stretch",
    )

    if summary["recent_refusals"]:
        st.write("Recent refusals")
        st.dataframe(
            [
                {"Question": entry.question, "Message": entry.message}
                for entry in summary["recent_refusals"]
            ],
            hide_index=True,
            width="stretch",
        )


def state_coverage(rows: list[dict]) -> list[dict]:
    counts = Counter(row["state"] for row in rows)
    return [
        {"State": state, "County rows": count}
        for state, count in sorted(counts.items())
    ]


def measure_catalog(measures: list[Measure]) -> list[dict]:
    return [
        {
            "Measure ID": measure.id,
            "Label": measure.label,
            "Universe": measure.universe,
            "Plain language": measure.plain_language,
        }
        for measure in measures
    ]


def render_sidebar(rows: list[dict], layer, measures: list[Measure]) -> None:
    coverage = state_coverage(rows)
    st.header("Dataset")
    st.write(layer.dataset.get("name", "CDC PLACES"))
    st.write(f"Rows loaded: {len(rows):,}")
    st.write(f"Feedback backend: `{feedback_backend()}`")

    with st.expander("Geographic coverage", expanded=True):
        st.write(f"{len(coverage)} states/areas")
        st.write(f"{len({place_label(row) for row in rows}):,} county-level places")
        st.dataframe(coverage, hide_index=True, width="stretch", height=260)

    with st.expander("Data variables you can ask about", expanded=True):
        st.dataframe(measure_catalog(measures), hide_index=True, width="stretch", height=320)

    with st.expander("Question patterns", expanded=False):
        st.write("- Which counties have the highest uninsured rate?")
        st.write("- Which California counties have the lowest diabetes rates?")
        st.write("- Compare Fresno County, CA and Los Angeles County, CA on poor mental health.")
        st.write("- Summarize Harris County, TX.")
        st.write("- Explain uninsured.")

    st.divider()
    st.write("Allowed operations: rank, compare, summarize, explain.")


def main() -> None:
    load_streamlit_secrets()
    rows = cached_rows()
    layer = cached_layer()
    places = sorted({place_label(row) for row in rows})
    states = [""] + sorted({row["state"] for row in rows})
    measures = list(layer.measures.values())
    measure_by_label = {measure.label: measure for measure in measures}

    st.set_page_config(page_title="CDC PLACES Reporter Tool", layout="wide")
    st.title("CDC PLACES Reporter Tool")
    st.caption(
        "A semantic-layer prototype for asking safer reporter questions over county-level PLACES estimates."
    )

    with st.sidebar:
        render_sidebar(rows, layer, measures)

    ask_tab, rank_tab, compare_tab, explain_tab, feedback_tab = st.tabs(
        ["Ask", "Rank", "Compare", "Explain", "Feedback"]
    )

    with ask_tab:
        parser_label = st.radio(
            "Parser",
            ["Rules", "Local LLM via Ollama", "OpenAI", "Auto fallback"],
            horizontal=True,
            help="The LLM only parses intent JSON. The semantic layer still validates and executes the query.",
        )
        parser = {
            "Rules": "rules",
            "Local LLM via Ollama": "ollama",
            "OpenAI": "openai",
            "Auto fallback": "auto",
        }[parser_label]
        question = st.text_area(
            "Plain-English question",
            value="Which California counties have the highest uninsured rates?",
            height=110,
        )
        if st.button("Ask", type="primary"):
            answer = route_question(question, rows, layer, parser=parser)
            log_routed_question(question, answer)
            if not answer.ok:
                st.warning(answer.message)
            elif answer.operation == "explain" and answer.measure:
                render_text_answer(measure_to_text(layer, answer.measure))
            elif answer.result:
                render_text_answer(result_to_text(answer.result, layer))

    with rank_tab:
        cols = st.columns([2, 1, 1, 1])
        selected_measure_label = cols[0].selectbox("Measure", list(measure_by_label))
        selected_state = cols[1].selectbox("State", states, index=0, format_func=lambda value: value or "All")
        direction = cols[2].selectbox("Direction", ["Highest", "Lowest"])
        limit = cols[3].number_input("Rows", min_value=1, max_value=25, value=10)
        if st.button("Run ranking"):
            measure = measure_by_label[selected_measure_label]
            result = rank(
                rows,
                layer,
                measure.id,
                state=selected_state or None,
                limit=int(limit),
                descending=direction == "Highest",
            )
            render_rank_table(result)
            render_cautions(layer, measure)

    with compare_tab:
        cols = st.columns([1, 1, 1])
        place_one = cols[0].selectbox("First place", places, index=0)
        place_two = cols[1].selectbox("Second place", places, index=min(1, len(places) - 1))
        compare_measure_label = cols[2].selectbox("Compare measure", list(measure_by_label), key="compare_measure")
        if st.button("Compare places"):
            measure = measure_by_label[compare_measure_label]
            result = compare(rows, layer, measure.id, [place_one, place_two])
            render_compare_table(result)
            render_cautions(layer, measure)

    with explain_tab:
        explain_measure_label = st.selectbox("Measure to explain", list(measure_by_label), key="explain_measure")
        measure = measure_by_label[explain_measure_label]
        render_text_answer(measure_to_text(layer, measure))

        place = st.selectbox("Optional county profile", places)
        if st.button("Summarize selected county"):
            result = summarize(rows, layer, place)
            render_summary_table(result)
            render_cautions(layer)

    with feedback_tab:
        render_feedback_summary()


if __name__ == "__main__":
    main()
