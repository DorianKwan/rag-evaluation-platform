import asyncio
import logging
import math

from anthropic import AsyncAnthropic
from openai import AsyncOpenAI
from ragas.embeddings.base import BaseRagasEmbedding, embedding_factory
from ragas.llms import llm_factory
from ragas.llms.base import InstructorBaseRagasLLM
from ragas.metrics.collections import (
    AnswerRelevancy,
    ContextPrecision,
    ContextRecall,
    Faithfulness,
)

from app.config import settings
from app.contracts import SupportedMetric

logger = logging.getLogger(__name__)

# collections metrics use ascore() directly — not the evaluate()/EvaluationDataset pipeline.
# ascore field requirements per metric:
# faithfulness:      user_input, response, retrieved_contexts
# answer_relevancy:  user_input, response        (scores against user_input, NOT reference)
# context_precision: user_input, reference, retrieved_contexts
# context_recall:    user_input, retrieved_contexts, reference


def _get_llm() -> InstructorBaseRagasLLM:
    client = AsyncAnthropic(api_key=settings.anthropic_api_key)
    llm = llm_factory(settings.ragas_judge_model, provider="anthropic", client=client)
    # RAGAS sends both temperature and top_p by default; Anthropic rejects requests with both set.
    llm.model_args.pop("top_p", None)  # type: ignore[attr-defined]
    return llm


def _get_embeddings() -> BaseRagasEmbedding:
    client = AsyncOpenAI(api_key=settings.openai_api_key)
    return embedding_factory("openai", settings.ragas_embeddings_model, client=client)


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
    llm = _get_llm()
    embeddings = _get_embeddings()

    faithfulness = Faithfulness(llm=llm)
    answer_relevancy = AnswerRelevancy(llm=llm, embeddings=embeddings)
    context_precision = ContextPrecision(llm=llm)
    context_recall = ContextRecall(llm=llm)

    results = await asyncio.gather(
        faithfulness.ascore(user_input=user_input, response=answer, retrieved_contexts=retrieved_contexts),
        answer_relevancy.ascore(user_input=user_input, response=answer),
        context_precision.ascore(user_input=user_input, reference=reference, retrieved_contexts=retrieved_contexts),
        context_recall.ascore(user_input=user_input, retrieved_contexts=retrieved_contexts, reference=reference),
        return_exceptions=True,
    )

    raw_scores = zip(
        [SupportedMetric.faithfulness, SupportedMetric.answer_relevancy, SupportedMetric.context_precision, SupportedMetric.context_recall],
        results,
    )
    scores: dict[SupportedMetric, float | None] = {}
    for metric, r in raw_scores:
        if isinstance(r, BaseException):
            logger.warning("Metric %s failed: %s: %s", metric.value, type(r).__name__, r)
            scores[metric] = None
        else:
            scores[metric] = _nan_to_none(float(r.value))
    return scores
