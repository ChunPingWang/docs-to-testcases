import httpx

from app.config import settings
from app.core.runtime_settings import runtime_settings


async def embed_texts(texts: list[str], model: str | None = None) -> list[list[float]]:
    """Generate embeddings for a list of texts using Ollama."""
    model = model or runtime_settings.embedding_model
    embeddings = []

    async with httpx.AsyncClient(timeout=60.0) as client:
        # Batch in groups of 50
        for i in range(0, len(texts), 50):
            batch = texts[i : i + 50]
            for text in batch:
                resp = await client.post(
                    f"{settings.ollama_base_url}/api/embed",
                    json={"model": model, "input": text},
                )
                resp.raise_for_status()
                data = resp.json()
                embeddings.append(data["embeddings"][0])

    return embeddings


async def embed_single(text: str, model: str | None = None) -> list[float]:
    """Generate embedding for a single text."""
    result = await embed_texts([text], model)
    return result[0]
