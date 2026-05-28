import os

# Must be set before any app module is imported — Settings() runs at import time
os.environ.setdefault("ANTHROPIC_API_KEY", "test-key")
os.environ.setdefault("RAG_BOT_BASE_URL", "http://test-rag-bot")
os.environ.setdefault("RAG_BOT_API_KEY", "test-rag-key")

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def app_client():
    from app.main import app

    with TestClient(app) as c:
        yield c
