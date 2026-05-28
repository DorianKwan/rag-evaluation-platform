from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest
from fastapi import HTTPException

import app.services.rag_client as rag_client_module
from app.services.rag_client import fetch_rag_response


@pytest.fixture(autouse=True)
def mock_http_client(monkeypatch):
    client = MagicMock(spec=httpx.AsyncClient)
    monkeypatch.setattr(rag_client_module, "http_client", client)
    return client


async def test_fetch_returns_rag_response(mock_http_client):
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {
        "answer": "test answer",
        "context": ["ctx1", "ctx2"],
    }
    mock_http_client.post = AsyncMock(return_value=mock_response)

    result = await fetch_rag_response("what is X?")

    assert result.answer == "test answer"
    assert result.context == ["ctx1", "ctx2"]


async def test_fetch_raises_502_on_http_error(mock_http_client):
    error_response = MagicMock()
    error_response.status_code = 500
    error_response.text = "Internal Server Error"
    mock_http_client.post = AsyncMock(
        side_effect=httpx.HTTPStatusError(
            "", request=MagicMock(), response=error_response
        )
    )

    with pytest.raises(HTTPException) as exc:
        await fetch_rag_response("query")

    assert exc.value.status_code == 502
    assert "500" in exc.value.detail


async def test_fetch_raises_502_on_connection_error(mock_http_client):
    mock_http_client.post = AsyncMock(
        side_effect=httpx.ConnectError("connection refused")
    )

    with pytest.raises(HTTPException) as exc:
        await fetch_rag_response("query")

    assert exc.value.status_code == 502
    assert "unreachable" in exc.value.detail
