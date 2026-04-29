from cdc_places_tool.data import load_rows
from cdc_places_tool.query import compare, rank, summarize
from cdc_places_tool.semantic import load_semantic_layer


def test_rank_filters_state():
    rows = load_rows()
    layer = load_semantic_layer()
    result = rank(rows, layer, "diabetes", state="CA", limit=2)
    assert len(result["rows"]) == 2
    assert all(row["state"] == "CA" for row in result["rows"])
    assert result["rows"][0]["diabetes"] >= result["rows"][1]["diabetes"]


def test_rank_can_sort_lowest_first():
    rows = load_rows()
    layer = load_semantic_layer()
    result = rank(rows, layer, "diabetes", state="CA", limit=2, descending=False)
    assert result["rows"][0]["diabetes"] <= result["rows"][1]["diabetes"]


def test_rank_skips_missing_values():
    rows = [
        {"state": "CA", "county": "Alpha County", "geoid": "1", "diabetes": ""},
        {"state": "CA", "county": "Beta County", "geoid": "2", "diabetes": 8.2},
    ]
    layer = load_semantic_layer()
    result = rank(rows, layer, "diabetes", state="CA")
    assert len(result["rows"]) == 1
    assert result["rows"][0]["county"] == "Beta County"


def test_compare_matches_places():
    rows = load_rows()
    layer = load_semantic_layer()
    result = compare(rows, layer, "uninsured", ["Fresno County, CA", "Los Angeles County, CA"])
    assert {row["county"] for row in result["rows"]} == {"Fresno County", "Los Angeles County"}


def test_summarize_place():
    rows = load_rows()
    layer = load_semantic_layer()
    result = summarize(rows, layer, "Fresno County, CA")
    assert result["place"]["county"] == "Fresno County"
    assert result["values"]
