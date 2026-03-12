import httpx

from app.config import settings
from app.core.runtime_settings import runtime_settings


async def embed_texts(
    texts: list[str],
    model: str | None = None,
    embed_type: str = "db",
) -> list[list[float]]:
    """Generate embeddings using MiniMax API.

    Args:
        texts: List of texts to embed.
        model: Embedding model name (default: from runtime settings).
        embed_type: "db" for document storage, "query" for search queries.
    """
    model = model or runtime_settings.embedding_model

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {settings.llm_api_key}",
    }

    embeddings = []

    # Batch in groups of 50
    for i in range(0, len(texts), 50):
        batch = texts[i : i + 50]
        payload = {
            "model": model,
            "texts": batch,
            "type": embed_type,
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{settings.llm_api_base_url}/embeddings",
                headers=headers,
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()

            # MiniMax returns {vectors: [...], base_resp: {status_code, status_msg}}
            base_resp = data.get("base_resp", {})
            if base_resp.get("status_code", 0) != 0:
                raise RuntimeError(
                    f"Embedding API error: {base_resp.get('status_msg', 'unknown')}"
                )

            vectors = data.get("vectors", [])
            embeddings.extend(vectors)

    return embeddings


async def embed_single(text: str, model: str | None = None) -> list[float]:
    """Generate embedding for a single text (query mode)."""
    result = await embed_texts([text], model, embed_type="query")
    return result[0]
