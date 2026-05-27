import math
from ragas import EvaluationDataset, SingleTurnSample, evaluate
from ragas.metrics.collections import (
    Faithfulness,
    AnswerRelevancy,
    ContextPrecision,
    ContextRecall,
)
from langchain_anthropic import ChatAnthropic
from app.config import settings
from app.contracts import SupportedMetric

# RAGAS metric → required SingleTurnSample fields:
# faithfulness:      user_input, response, retrieved_contexts
# answer_relevancy:  user_input, response
# context_precision: user_input, retrieved_contexts, reference
# context_recall:    retrieved_contexts, reference
# All fields are provided for every call — RAGAS ignores extras per metric.

_METRIC_KEY_MAP: dict[str, SupportedMetric] = {
    "faithfulness": SupportedMetric.faithfulness,
    "answer_relevancy": SupportedMetric.answer_relevancy,
    "context_precision": SupportedMetric.context_precision,
    "context_recall": SupportedMetric.context_recall,
}


def _get_llm() -> ChatAnthropic:
    return ChatAnthropic(
        model=settings.ragas_judge_model,
        api_key=settings.anthropic_api_key,
    )


def _nan_to_none(value: float | None) -> float | None:
    """Convert NaN to None. 0.0 is a valid score and must be preserved."""
    if value is None:
        return None
    return None if math.isnan(value) else value


async def score(
    user_input: str,
    answer: str,
    retrieved_contexts: list[str],
    reference: str,
) -> dict[SupportedMetric, float | None]:
    """
    Run all four RAGAS metrics and return scores.
    NaN results → None. Metric failures → None (logged, not raised).
    """
    llm = _get_llm()
    metrics = [
        Faithfulness(llm=llm),
        AnswerRelevancy(llm=llm),
        ContextPrecision(llm=llm),
        ContextRecall(llm=llm),
    ]
    sample = SingleTurnSample(
        user_input=user_input,
        response=answer,
        retrieved_contexts=retrieved_contexts,
        reference=reference,
    )
    dataset = EvaluationDataset(samples=[sample])

    result = await evaluate(dataset=dataset, metrics=metrics)

    scores: dict[SupportedMetric, float | None] = {}
    result_dict = result.to_pandas().iloc[0].to_dict()

    for ragas_key, metric_enum in _METRIC_KEY_MAP.items():
        raw = result_dict.get(ragas_key)
        scores[metric_enum] = _nan_to_none(float(raw) if raw is not None else None)

    return scores
