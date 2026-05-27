import httpx
from fastapi import HTTPException
from app.config import settings
from app.contracts import RagBotResponse

# Module-level client — lifecycle managed by FastAPI lifespan in main.py
http_client: httpx.AsyncClient | None = None


def get_client() -> httpx.AsyncClient:
    if http_client is None:
        raise RuntimeError("HTTP client not initialized — lifespan not started")
    return http_client


async def fetch_rag_response(user_input: str) -> RagBotResponse:
    client = get_client()
    try:
        response = await client.post(
            f"{settings.rag_bot_base_url}/api/eval",
            json={"query": user_input},
            headers={"x-eval-api-key": settings.rag_bot_api_key},
        )
        response.raise_for_status()
        return RagBotResponse.model_validate(response.json())
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=502,
            detail=f"RAG bot returned {e.response.status_code}: {e.response.text[:200]}",
        ) from e
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=502,
            detail=f"RAG bot unreachable: {e}",
        ) from e
