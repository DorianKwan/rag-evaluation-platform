import pytest
from pydantic import ValidationError

from app.contracts import EvaluateRequest, EvaluateResponse, SupportedMetric


def test_evaluate_request_valid():
    req = EvaluateRequest(user_input="hello", reference="world")
    assert req.user_input == "hello"
    assert req.reference == "world"
    assert req.trace_id is None


def test_evaluate_request_with_trace_id():
    req = EvaluateRequest(user_input="hello", reference="world", trace_id="abc-123")
    assert req.trace_id == "abc-123"


def test_evaluate_request_rejects_empty_user_input():
    with pytest.raises(ValidationError):
        EvaluateRequest(user_input="", reference="world")


def test_evaluate_request_rejects_empty_reference():
    with pytest.raises(ValidationError):
        EvaluateRequest(user_input="hello", reference="")


def test_evaluate_response_preserves_zero():
    resp = EvaluateResponse(
        trace_id="abc",
        scores={
            SupportedMetric.faithfulness: 0.9,
            SupportedMetric.answer_relevancy: None,
            SupportedMetric.context_precision: 0.0,
            SupportedMetric.context_recall: 0.8,
        },
    )
    assert resp.scores[SupportedMetric.faithfulness] == 0.9
    assert resp.scores[SupportedMetric.answer_relevancy] is None
    assert resp.scores[SupportedMetric.context_precision] == 0.0  # 0.0 is a valid score
    assert resp.scores[SupportedMetric.context_recall] == 0.8
