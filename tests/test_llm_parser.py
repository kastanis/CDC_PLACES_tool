import json

from cdc_places_tool.llm_parser import (
    clean_state,
    extract_model_text,
    intent_from_json,
    parse_question_with_ollama,
    parse_question_with_openai,
)


def test_intent_from_json_cleans_fields():
    intent = intent_from_json(
        json.dumps(
            {
                "operation": "rank",
                "measure_id": "uninsured",
                "state": "ca",
                "direction": "lowest",
                "limit": "3",
                "confidence": "high",
            }
        )
    )
    assert intent.operation == "rank"
    assert intent.measure_id == "uninsured"
    assert intent.state == "CA"
    assert intent.direction == "lowest"
    assert intent.limit == 3


def test_clean_state_rejects_national_or_invalid_values():
    assert clean_state("US") is None
    assert clean_state("all") is None
    assert clean_state("ZZ") is None
    assert clean_state("CA") == "CA"


def test_parse_question_with_ollama_payload(monkeypatch):
    captured = {}

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["timeout"] = timeout
        captured["payload"] = json.loads(request.data.decode("utf-8"))
        return FakeResponse()

    def fake_json_load(response):
        return {
            "message": {
                "content": json.dumps(
                    {
                        "operation": "rank",
                        "measure_id": "diabetes",
                        "state": "TX",
                        "direction": "highest",
                        "limit": 5,
                    }
                )
            }
        }

    monkeypatch.setenv("OLLAMA_URL", "http://localhost:11434")
    monkeypatch.setenv("OLLAMA_MODEL", "test-model")
    monkeypatch.setenv("OLLAMA_TIMEOUT", "20")
    monkeypatch.setattr("cdc_places_tool.llm_parser.urlopen", fake_urlopen)
    monkeypatch.setattr("cdc_places_tool.llm_parser.json.load", fake_json_load)

    from cdc_places_tool.semantic import load_semantic_layer

    intent = parse_question_with_ollama("top diabetes in Texas", load_semantic_layer())
    assert captured["url"] == "http://localhost:11434/api/chat"
    assert captured["payload"]["model"] == "test-model"
    assert captured["payload"]["stream"] is False
    assert captured["payload"]["format"] == "json"
    assert "Use operation=rank" in captured["payload"]["messages"][0]["content"]
    assert intent.measure_id == "diabetes"


def test_parse_question_with_openai_payload(monkeypatch):
    captured = {}

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["headers"] = dict(request.header_items())
        captured["payload"] = json.loads(request.data.decode("utf-8"))
        return FakeResponse()

    def fake_json_load(response):
        return {
            "output_text": json.dumps(
                {
                    "operation": "rank",
                    "measure_id": "uninsured",
                    "state": "CA",
                    "direction": "highest",
                    "limit": 10,
                    "confidence": "high",
                }
            )
        }

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_MODEL", "test-openai-model")
    monkeypatch.setattr("cdc_places_tool.llm_parser.urlopen", fake_urlopen)
    monkeypatch.setattr("cdc_places_tool.llm_parser.json.load", fake_json_load)

    from cdc_places_tool.semantic import load_semantic_layer

    intent = parse_question_with_openai("insurance access in ca", load_semantic_layer())
    assert captured["url"] == "https://api.openai.com/v1/responses"
    assert captured["payload"]["model"] == "test-openai-model"
    assert captured["payload"]["text"]["format"]["type"] == "json_schema"
    assert intent.measure_id == "uninsured"


def test_extract_model_text_from_responses_output_shape():
    text = extract_model_text(
        {
            "output": [
                {
                    "content": [
                        {
                            "type": "output_text",
                            "text": '{"operation":"unsupported"}',
                        }
                    ]
                }
            ]
        }
    )
    assert text == '{"operation":"unsupported"}'
