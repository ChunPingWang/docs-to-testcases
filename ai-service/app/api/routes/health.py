from fastapi import APIRouter
import httpx

from app.config import settings
from app.models.responses import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    ollama_connected = False
    models_available = []
    chroma_connected = False

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{settings.ollama_base_url}/api/tags")
            if resp.status_code == 200:
                ollama_connected = True
                data = resp.json()
                models_available = [m["name"] for m in data.get("models", [])]
    except Exception:
        pass

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(
                f"http://{settings.chroma_host}:{settings.chroma_port}/api/v1/heartbeat"
            )
            if resp.status_code == 200:
                chroma_connected = True
    except Exception:
        pass

    return HealthResponse(
        status="ok",
        ollama_connected=ollama_connected,
        chroma_connected=chroma_connected,
        models_available=models_available,
    )


@router.get("/models")
async def list_models():
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{settings.ollama_base_url}/api/tags")
            resp.raise_for_status()
            return resp.json()
    except Exception as e:
        return {"error": str(e), "models": []}
