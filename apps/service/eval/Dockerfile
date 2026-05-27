FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv
COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-dev

COPY patches/ ./patches/

RUN cp patches/lc_vertexai_stub.py \
    .venv/lib/python3.12/site-packages/langchain_community/chat_models/vertexai.py

COPY app/ ./app/

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
