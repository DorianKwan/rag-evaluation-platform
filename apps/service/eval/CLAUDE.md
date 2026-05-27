# @/eval — RAG Eval Service

Python FastAPI service. Stateless. One job per test case. Receives a golden pair from the BullMQ
orchestration layer, calls the RAG bot to get its answer and retrieved context, runs RAGAS scoring,
and returns scores. No DB. No queue management. No result storage.

## Request flow

```
BullMQ → POST /evaluate {user_input, reference, trace_id?}
  → httpx → RAG bot POST /api/eval {query: user_input}
  ← RAG bot {answer, context: string[]}
  → RAGAS score(user_input, answer, reference, context)
  ← {trace_id, scores: {metric: float|null}}
```

The incoming request does **not** include `retrieved_contexts` — the service fetches both the answer
and retrieved context from the RAG bot itself. The RAG bot is the authoritative source.

## Stack

- Python 3.12, FastAPI + Uvicorn
- RAGAS (v0.2+ API — `SingleTurnSample`, `EvaluationDataset`, `evaluate()`)
- `langchain-anthropic` for the RAGAS judge LLM
- `httpx.AsyncClient` for RAG bot calls
- Pydantic v2 + pydantic-settings
- `uv` / `pyproject.toml`

## Target folder structure

```
apps/service/eval/
├── pyproject.toml
├── uv.lock
├── Dockerfile
├── .env.example
└── app/
    ├── main.py            # FastAPI app init, router registration, lifespan
    ├── contracts.py       # Pydantic models
    ├── config.py          # pydantic-settings; validates env vars on startup
    ├── routes/
    │   ├── __init__.py
    │   ├── evaluate.py    # POST /evaluate — orchestrates RAG fetch + RAGAS score
    │   └── health.py      # GET /health
    └── services/
        ├── __init__.py
        ├── rag_client.py  # httpx async client; lifespan wiring; 502 on failure
        └── scorer.py      # RAGAS integration; NaN → null; field-to-metric comments
```

## Pydantic contracts

```python
# app/contracts.py

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class SupportedMetric(str, Enum):
    faithfulness = "faithfulness"
    answer_relevancy = "answer_relevancy"
    context_precision = "context_precision"
    context_recall = "context_recall"


class EvaluateRequest(BaseModel):
    user_input: str = Field(..., min_length=1)
    reference: str = Field(..., min_length=1)
    trace_id: Optional[str] = None


class EvaluateResponse(BaseModel):
    trace_id: str          # UUID4-generated if not provided by caller
    scores: dict[SupportedMetric, Optional[float]]


class HealthResponse(BaseModel):
    status: str            # always "ok"


# Internal — not exposed in API response
class RagBotResponse(BaseModel):
    answer: str
    context: list[str]
```

## API surface

### POST /evaluate

| Status | Meaning |
|--------|---------|
| 200 | Scores returned; individual metrics may be `null` |
| 422 | Pydantic validation error (FastAPI default) |
| 502 | RAG bot unreachable or returned non-2xx |
| 504 | Total eval (RAG call + RAGAS) exceeded `EVAL_TIMEOUT_SECONDS` |

### GET /health

Returns `{"status": "ok"}` unconditionally. Used by Docker Compose health checks.

## Environment variables

```bash
ANTHROPIC_API_KEY=
RAGAS_JUDGE_MODEL=claude-haiku-4-5   # configurable; Haiku default

RAG_BOT_BASE_URL=http://next-app:3000
RAG_BOT_API_KEY=                      # sent as x-eval-api-key header

EVAL_TIMEOUT_SECONDS=120
```

## Critical invariants

**NaN → null, never 0.0**
If RAGAS returns `float('nan')` or raises on a specific metric, that metric's score is `null`
in the response. `0.0` is a valid real score and must never be used as a sentinel.

**All four metrics always run**
`faithfulness`, `answer_relevancy`, `context_precision`, `context_recall` — always. The caller
does not select metrics. A metric scoring `null` is still present in the response.

**RAGAS v0.2+ API only**
Use `SingleTurnSample`, `EvaluationDataset`, `evaluate()`. Never use the v0.1 dict-based API.
Pin the exact RAGAS version in `pyproject.toml` — RAGAS has had breaking changes between minors.

**RAGAS field semantics — document in scorer.py**
```
faithfulness       → user_input, response, retrieved_contexts
answer_relevancy   → user_input, response        (NOT reference — scores against user_input)
context_precision  → user_input, retrieved_contexts, reference
context_recall     → user_input, retrieved_contexts, reference
```
Add a comment block in `scorer.py` with this mapping so future changes don't silently drop
required fields or misattribute metric behavior.

**Single global timeout via `asyncio.wait_for`**
Wraps the entire evaluate handler body (RAG call + RAGAS scoring). Returns 504 on
`asyncio.TimeoutError`. Log a warning on `asyncio.CancelledError` — RAGAS may not cancel
cleanly if it runs blocking LangChain internals in a thread pool.

**httpx.AsyncClient is a shared instance**
Create once in FastAPI lifespan startup, close on shutdown. Never instantiate per-request.

**No auth**
Network isolation via Docker Compose is the security boundary. Do not add API key validation
to the eval service endpoints.

**Log trace_id on every request**
Emit `trace_id` in structured logs on request receipt and on response. It is the correlation
key between eval scores and upstream LLM traces.

## Never do these

- Access a database or import Prisma — this service is stateless, no DB ever
- Store eval results — storage is the caller's responsibility
- Accept multiple pairs in one request — one call = one pair
- Expose routes beyond `POST /evaluate` and `GET /health`
- Return `0.0` for a failed metric — use `null`
- Use the RAGAS v0.1 dict-based API
- Leave RAGAS version unpinned in `pyproject.toml`
- Create the httpx client per-request

## Implementation order

1. **Scaffold** — `pyproject.toml`, install deps (`uv add ragas langchain-anthropic httpx pydantic-settings fastapi uvicorn`), confirm `import ragas` works. Then folder structure, `Dockerfile`, `.env.example`.
2. **Config** — `app/config.py` with pydantic-settings; validate all env vars on startup.
3. **Contracts** — `app/contracts.py`; exact models above.
4. **RAG client** — `app/services/rag_client.py`; shared httpx client, lifespan wiring, 502 mapping.
5. **Scorer** — `app/services/scorer.py`; RAGAS integration, field-to-metric comment block, NaN → null.
6. **Routes** — `app/routes/evaluate.py` (timeout wrapper, client + scorer calls) + `app/routes/health.py`.
7. **App entrypoint** — `app/main.py`; lifespan, router registration.
8. **Docker Compose** — add `eval-service` to existing `docker-compose.yml`.

## Monorepo position

This service has a stub `package.json` (uv shim) so Turborepo can reference it in the workspace
graph. `turbo run build` does not execute Python tasks. Python dev and test are managed via `uv`
directly.

```bash
cd apps/service/eval
uv run fastapi dev        # local dev
uv run pytest             # tests (once test suite exists)
```

`@/eval` never imports from other monorepo packages. The TS↔Python boundary is defined by
`libs/contracts` — the Pydantic models above are the Python side of that contract. Any change
to the request/response shape must also update the Zod schema in `libs/contracts`.
