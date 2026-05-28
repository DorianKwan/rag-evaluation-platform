import asyncio
import logging
import uuid

from fastapi import APIRouter, HTTPException

from app.config import settings
from app.contracts import EvaluateRequest, EvaluateResponse
from app.services.rag_client import fetch_rag_response
from app.services.scorer import score

logger = logging.getLogger(__name__)
router = APIRouter()


async def _run_evaluation(request: EvaluateRequest) -> EvaluateResponse:
    trace_id = request.trace_id or str(uuid.uuid4())
    logger.info("Evaluation started", extra={"trace_id": trace_id})

    rag_response = await fetch_rag_response(request.user_input)

    scores = await score(
        user_input=request.user_input,
        answer=rag_response.answer,
        retrieved_contexts=rag_response.context,
        reference=request.reference,
    )

    logger.info("Evaluation complete", extra={"trace_id": trace_id, "scores": scores})
    return EvaluateResponse(trace_id=trace_id, scores=scores)


@router.post("/evaluate", response_model=EvaluateResponse)
async def evaluate_endpoint(request: EvaluateRequest) -> EvaluateResponse:
    try:
        return await asyncio.wait_for(
            _run_evaluation(request),
            timeout=settings.eval_timeout_seconds,
        )
    except TimeoutError:
        raise HTTPException(status_code=504, detail="Evaluation timed out")
