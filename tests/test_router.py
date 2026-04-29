from cdc_places_tool.data import load_rows
from cdc_places_tool.router import route_question
from cdc_places_tool.semantic import load_semantic_layer


def test_routes_rank_question():
    answer = route_question(
        "Which California counties have the highest uninsured rates?",
        load_rows(),
        load_semantic_layer(),
    )
    assert answer.ok
    assert answer.operation == "rank"
    assert answer.result["measure"].id == "uninsured"


def test_routes_compare_question():
    answer = route_question(
        "Compare Fresno County, CA and Los Angeles County, CA on poor mental health",
        load_rows(),
        load_semantic_layer(),
    )
    assert answer.ok
    assert answer.operation == "compare"
    assert len(answer.result["rows"]) == 2


def test_refuses_causal_question():
    answer = route_question(
        "Did uninsured rates cause poor mental health in Fresno County?",
        load_rows(),
        load_semantic_layer(),
    )
    assert not answer.ok
    assert "causal" in answer.message


def test_routes_lowest_question():
    answer = route_question(
        "Which California counties have the lowest diabetes rates?",
        load_rows(),
        load_semantic_layer(),
    )
    assert answer.ok
    assert answer.result["headline"].startswith("Lowest")
