from cdc_places_tool.guardrails import check_question


def test_refuses_count_conversion():
    allowed, message = check_question("How many people in Fresno County have diabetes?")
    assert not allowed
    assert "prevalence" in message


def test_allows_rank_question():
    allowed, message = check_question("Which counties have the highest diabetes rates?")
    assert allowed
    assert message is None
