from cdc_places_tool.semantic import load_semantic_layer


def test_loads_measures():
    layer = load_semantic_layer()
    assert "diabetes" in layer.measures
    assert layer.get_measure("diabetes").label == "Diagnosed diabetes among adults"


def test_synonym_lookup():
    layer = load_semantic_layer()
    assert layer.get_measure("poor mental health").id == "poor_mental_health"

