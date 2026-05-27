from contextlib import asynccontextmanager
import httpx
from fastapi import FastAPI
import app.services.rag_client as rag_client
from app.routes import evaluate, health


@asynccontextmanager
async def lifespan(app: FastAPI):
    rag_client.http_client = httpx.AsyncClient(timeout=30.0)
    yield
    await rag_client.http_client.aclose()
    rag_client.http_client = None


app = FastAPI(title="RAG Eval Service", lifespan=lifespan)
app.include_router(health.router)
app.include_router(evaluate.router)
