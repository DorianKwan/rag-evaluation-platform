# @/eval — RAG Eval Service

Python FastAPI service. Stateless. Receives a golden pair, calls the RAG bot, runs RAGAS scoring, returns scores.

## Local dev setup

### Prerequisites

- Python 3.12
- [`uv`](https://docs.astral.sh/uv/) — install via `curl -LsSf https://astral.sh/uv/install.sh | sh`

### 1. Install dependencies

```bash
cd apps/service/eval
uv sync
```

### 2. Apply the vertexai stub patch

RAGAS has a broken top-level import for `langchain_community.chat_models.vertexai` (removed in `langchain-community 0.4.x`). Apply this patch after every fresh `uv sync`:

#### 2.1 Create Virtual Environment

```bash
cp patches/lc_vertexai_stub.py .venv/lib/python3.12/site-packages/langchain_community/chat_models/vertexai.py
```

> **Note:** This must be re-applied any time `.venv` is recreated (e.g. after `uv sync --reinstall` or deleting `.venv`).

### 3. Configure environment

```bash
cp .env.example .env
```

Fill in the required values in `.env`:

| Variable                 | Required | Default                    | Description                                                   |
| ------------------------ | -------- | -------------------------- | ------------------------------------------------------------- |
| `ANTHROPIC_API_KEY`      | yes      | —                          | Anthropic API key — used as the RAGAS judge LLM               |
| `OPENAI_API_KEY`         | yes      | —                          | OpenAI API key — used for `AnswerRelevancy` embeddings only   |
| `RAG_BOT_BASE_URL`       | yes      | —                          | Base URL of the RAG bot.                                      |
| `RAG_BOT_API_KEY`        | yes      | —                          | Sent as `x-eval-api-key` header to the RAG bot                |
| `RAGAS_JUDGE_MODEL`      | no       | `claude-haiku-4-5`         | Claude model used as RAGAS judge LLM                          |
| `RAGAS_EMBEDDINGS_MODEL` | no       | `text-embedding-3-small`   | OpenAI embeddings model used for `AnswerRelevancy`            |
| `EVAL_TIMEOUT_SECONDS`   | no       | `120`                      | Total timeout for RAG call + scoring                          |

### 4. Verify config loads

```bash
uv run python -c "from app.config import settings; print(settings.model_dump())"
```

Should print all fields without error.

### 5. Start the dev server

```bash
uv run fastapi dev
```

Service runs on `http://localhost:8000`. Hot-reloads on file changes.

## Endpoints

| Method | Path        | Description                         |
| ------ | ----------- | ----------------------------------- |
| `GET`  | `/health`   | Returns `{"status": "ok"}`          |
| `POST` | `/evaluate` | Runs RAGAS eval for one golden pair |

## Known issues

- **`uv` not in default PATH on some systems.** If `uv` is not found, use the full path: `~/.local/bin/uv run ...`
- **vertexai stub is ephemeral.** Must be re-applied after any fresh `uv sync`. See step 2 above.
