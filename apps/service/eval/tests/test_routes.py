from unittest.mock import AsyncMock, patch

from app.contracts import EvaluateResponse, SupportedMetric


def test_health(app_client):
    resp = app_client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_evaluate_returns_scores(app_client):
    fake_response = EvaluateResponse(
        trace_id="trace-abc",
        scores={
            SupportedMetric.faithfulness: 0.9,
            SupportedMetric.answer_relevancy: 0.8,
            SupportedMetric.context_precision: None,
            SupportedMetric.context_recall: 0.7,
        },
    )

    with patch(
        "app.routes.evaluate._run_evaluation",
        new_callable=AsyncMock,
        return_value=fake_response,
    ):
        resp = app_client.post(
            "/evaluate",
            json={"user_input": "test question", "reference": "expected answer"},
        )

    assert resp.status_code == 200
    body = resp.json()
    assert body["trace_id"] == "trace-abc"
    assert body["scores"]["faithfulness"] == 0.9
    assert body["scores"]["context_precision"] is None


def test_evaluate_returns_504_on_timeout(app_client):
    # Raise TimeoutError from _run_evaluation itself — cleaner than patching wait_for
    # since it avoids a stale unawaited coroutine from the real function.
    async def raise_timeout(_request):
        raise TimeoutError()

    with patch("app.routes.evaluate._run_evaluation", raise_timeout):
        resp = app_client.post(
            "/evaluate",
            json={"user_input": "test question", "reference": "expected answer"},
        )

    assert resp.status_code == 504


def test_evaluate_rejects_invalid_body(app_client):
    resp = app_client.post("/evaluate", json={"user_input": "", "reference": "ref"})
    assert resp.status_code == 422
