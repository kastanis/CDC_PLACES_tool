from cdc_places_tool.feedback import log_question, summarize_question_log


def test_logs_and_summarizes_questions(tmp_path):
    log_path = tmp_path / "questions.jsonl"
    log_question(
        question="Which counties have the highest diabetes rates?",
        ok=True,
        operation="rank",
        measure_id="diabetes",
        message="Highest diagnosed diabetes among adults values",
        path=log_path,
    )
    log_question(
        question="Did diabetes cause obesity?",
        ok=False,
        operation=None,
        measure_id=None,
        message="No causal claims.",
        path=log_path,
    )

    summary = summarize_question_log(log_path)
    assert summary["total_questions"] == 2
    assert summary["accepted_questions"] == 1
    assert summary["refused_questions"] == 1
    assert summary["operations"][0] == ("rank", 1)
