from unittest.mock import AsyncMock, MagicMock, patch

from app.contracts import SupportedMetric
from app.services.scorer import _nan_to_none, score


def test_nan_to_none_converts_nan():
    assert _nan_to_none(float("nan")) is None


def test_nan_to_none_preserves_zero():
    assert _nan_to_none(0.0) == 0.0


def test_nan_to_none_preserves_valid_float():
    assert _nan_to_none(0.87) == 0.87


def test_nan_to_none_passes_through_none():
    assert _nan_to_none(None) is None


def _scorer_mocks(result_dict: dict):
    """Shared context manager that mocks all RAGAS I/O in scorer.score()."""
    mock_df = MagicMock()
    mock_df.iloc[0].to_dict.return_value = result_dict
    mock_result = MagicMock()
    mock_result.to_pandas.return_value = mock_df

    from contextlib import ExitStack

    stack = ExitStack()
    # RAGAS metric classes validate the LLM type — mock them to skip that check
    for cls in ("Faithfulness", "AnswerRelevancy", "ContextPrecision", "ContextRecall"):
        stack.enter_context(patch(f"app.services.scorer.{cls}"))
    stack.enter_context(patch("app.services.scorer._get_llm", return_value=MagicMock()))
    stack.enter_context(
        patch(
            "app.services.scorer.evaluate",
            new_callable=AsyncMock,
            return_value=mock_result,
        )
    )
    return stack


async def test_score_maps_metrics_and_converts_nan():
    with _scorer_mocks(
        {
            "faithfulness": 0.9,
            "answer_relevancy": 0.8,
            "context_precision": float("nan"),
            "context_recall": 0.7,
        }
    ):
        result = await score(
            user_input="test question",
            answer="test answer",
            retrieved_contexts=["context chunk"],
            reference="expected answer",
        )

    assert result[SupportedMetric.faithfulness] == 0.9
    assert result[SupportedMetric.answer_relevancy] == 0.8
    assert result[SupportedMetric.context_precision] is None  # NaN → None
    assert result[SupportedMetric.context_recall] == 0.7


async def test_score_returns_none_for_missing_metric_key():
    with _scorer_mocks({}):  # all keys absent from result
        result = await score(
            user_input="q",
            answer="a",
            retrieved_contexts=[],
            reference="ref",
        )

    for metric in SupportedMetric:
        assert result[metric] is None
