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


def test_routes_explain_with_underscored_measure():
    answer = route_question(
        "explain poor_mental_health",
        load_rows(),
        load_semantic_layer(),
    )
    assert answer.ok
    assert answer.operation == "explain"
    assert answer.measure.id == "poor_mental_health"


def test_routes_with_ollama_parser(monkeypatch):
    from cdc_places_tool.llm_parser import ParsedIntent

    def fake_parse(question, layer):
        return ParsedIntent(
            operation="rank",
            measure_id="uninsured",
            state="CA",
            direction="highest",
            limit=3,
        )

    monkeypatch.setattr("cdc_places_tool.router.parse_question_with_ollama", fake_parse)
    answer = route_question(
        "show me the insurance problem in california",
        load_rows(),
        load_semantic_layer(),
        parser="ollama",
    )
    assert answer.ok
    assert answer.operation == "rank"
    assert len(answer.result["rows"]) == 3


def test_routes_with_openai_parser(monkeypatch):
    from cdc_places_tool.llm_parser import ParsedIntent

    def fake_parse(question, layer):
        return ParsedIntent(
            operation="explain",
            measure_id="poor_mental_health",
            state=None,
            direction=None,
            limit=None,
        )

    monkeypatch.setattr("cdc_places_tool.router.parse_question_with_openai", fake_parse)
    answer = route_question(
        "what is the mental health measure",
        load_rows(),
        load_semantic_layer(),
        parser="openai",
    )
    assert answer.ok
    assert answer.operation == "explain"
    assert answer.measure.id == "poor_mental_health"


def test_llm_national_state_does_not_filter_to_empty_rows(monkeypatch):
    from cdc_places_tool.llm_parser import ParsedIntent

    def fake_parse(question, layer):
        return ParsedIntent(
            operation="rank",
            measure_id="uninsured",
            state="US",
            direction="highest",
            limit=5,
        )

    monkeypatch.setattr("cdc_places_tool.router.parse_question_with_openai", fake_parse)
    answer = route_question(
        "Which counties have the highest uninsured rate?",
        load_rows(),
        load_semantic_layer(),
        parser="openai",
    )
    assert answer.ok
    assert answer.operation == "rank"
    assert len(answer.result["rows"]) == 5
