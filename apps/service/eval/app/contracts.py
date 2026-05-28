from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class SupportedMetric(StrEnum):
    faithfulness = "faithfulness"
    answer_relevancy = "answer_relevancy"
    context_precision = "context_precision"
    context_recall = "context_recall"


class EvaluateRequest(BaseModel):
    user_input: str = Field(..., min_length=1)
    reference: str = Field(..., min_length=1)
    trace_id: str | None = None


class EvaluateResponse(BaseModel):
    trace_id: str
    scores: dict[SupportedMetric, float | None]


class HealthResponse(BaseModel):
    status: str


# Internal — not part of the public API
class RagBotResponse(BaseModel):
    answer: str
    context: list[str]
