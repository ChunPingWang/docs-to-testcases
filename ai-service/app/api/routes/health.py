from fastapi import APIRouter
import httpx

from app.config import settings
from app.core.runtime_settings import runtime_settings
from app.models.responses import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    llm_api_connected = False
    models_available = []
    chroma_connected = False

    # Check LLM API connectivity with a minimal request
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{settings.llm_api_base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.llm_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": runtime_settings.llm_model,
                    "messages": [{"role": "user", "content": "ping"}],
                    "max_tokens": 1,
                },
            )
            if resp.status_code == 200:
                llm_api_connected = True
                models_available = [runtime_settings.llm_model, runtime_settings.embedding_model]
    except Exception:
        pass

    # Check ChromaDB connectivity
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(
                f"http://{settings.chroma_host}:{settings.chroma_port}/api/v2/heartbeat"
            )
            if resp.status_code == 200:
                chroma_connected = True
    except Exception:
        pass

    return HealthResponse(
        status="ok",
        llm_api_connected=llm_api_connected,
        chroma_connected=chroma_connected,
        models_available=models_available,
    )


@router.get("/models")
async def list_models():
    """Return configured models (MiniMax doesn't have a /models listing endpoint)."""
    return {
        "data": [
            {"id": runtime_settings.llm_model, "type": "llm"},
            {"id": runtime_settings.embedding_model, "type": "embedding"},
        ]
    }
