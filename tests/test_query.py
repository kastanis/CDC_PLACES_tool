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

