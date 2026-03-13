"""OpenAI-compatible embedding client — provider-aware.

Resolves base_url and api_key from the active provider in the registry.
"""

import asyncio
import logging

import httpx

from app.core.runtime_settings import runtime_settings

logger = logging.getLogger(__name__)

MAX_RETRIES = 8
RETRY_BASE_DELAY = 5  # seconds


def _resolve_provider():
    """Return (base_url, api_key, extra_headers) from active provider."""
    from app.core.llm.provider_registry import provider_registry
    p = provider_registry.get_active()
    if p:
        return p.base_url, p.api_key, p.extra_headers
    from app.config import settings
    return settings.llm_api_base_url, settings.llm_api_key, {}


async def _embed_batch(
    client: httpx.AsyncClient,
    texts: list[str],
    model: str,
    headers: dict,
    base_url: str,
) -> list[list[float]]:
    """Embed a single batch with retry on rate limit."""
    payload = {
        "model": model,
        "input": texts,
    }

    for attempt in range(MAX_RETRIES):
        resp = await client.post(
            f"{base_url}/embeddings",
            headers=headers,
            json=payload,
        )

        if resp.status_code == 429:
            delay = RETRY_BASE_DELAY * (attempt + 1)
            logger.warning(
                "Embedding rate limited (429), retrying in %ds (%d/%d)",
                delay, attempt + 1, MAX_RETRIES,
            )
            await asyncio.sleep(delay)
            continue

        resp.raise_for_status()
        data = resp.json()

        # OpenAI format: {data: [{embedding: [...], index: 0}, ...]}
        items = data["data"]
        if items and "index" in items[0]:
            items = sorted(items, key=lambda x: x["index"])
        return [item["embedding"] for item in items]

    raise RuntimeError("Embedding API rate limit: max retries exceeded")


async def embed_texts(
    texts: list[str],
    model: str | None = None,
    embed_type: str | None = None,  # kept for backward compatibility
) -> list[list[float]]:
    """Generate embeddings using OpenAI-compatible API with rate-limit retry."""
    model = model or runtime_settings.embedding_model
    base_url, api_key, extra = _resolve_provider()

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    if extra:
        headers.update(extra)

    embeddings = []
    batch_size = 20

    async with httpx.AsyncClient(timeout=120.0) as client:
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            vectors = await _embed_batch(client, batch, model, headers, base_url)
            embeddings.extend(vectors)
            logger.info("Embedded batch %d/%d", i // batch_size + 1, -(-len(texts) // batch_size))

    return embeddings


async def embed_single(text: str, model: str | None = None) -> list[float]:
    """Generate embedding for a single text."""
    result = await embed_texts([text], model)
    return result[0]
