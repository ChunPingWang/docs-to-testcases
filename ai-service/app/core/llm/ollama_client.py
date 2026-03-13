"""OpenAI-compatible LLM client — provider-aware.

Resolves base_url, api_key, and model from the active provider in the
provider registry.  All existing call-sites continue to work unchanged.
"""

import json
import re
from collections.abc import AsyncGenerator

import httpx

from app.core.runtime_settings import runtime_settings

_THINK_RE = re.compile(r"<think>.*?</think>\s*", re.DOTALL)


def _strip_think(text: str) -> str:
    """Strip <think>...</think> reasoning blocks from model output."""
    return _THINK_RE.sub("", text).strip()


def _resolve_provider():
    """Return (base_url, api_key, extra_headers) from active provider."""
    from app.core.llm.provider_registry import provider_registry
    p = provider_registry.get_active()
    if p:
        return p.base_url, p.api_key, p.extra_headers
    # Fallback to static config
    from app.config import settings
    return settings.llm_api_base_url, settings.llm_api_key, {}


def _headers() -> dict:
    _, api_key, extra = _resolve_provider()
    h = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    if extra:
        h.update(extra)
    return h


def _base_url() -> str:
    url, _, _ = _resolve_provider()
    return url


async def generate(
    prompt: str,
    system: str = "",
    model: str | None = None,
    temperature: float = 0.7,
    max_tokens: int = 4096,
) -> str:
    """Generate a response using OpenAI-compatible chat API."""
    model = model or runtime_settings.llm_model

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    return await chat(messages, model=model, temperature=temperature, max_tokens=max_tokens)


async def generate_stream(
    prompt: str,
    system: str = "",
    model: str | None = None,
    temperature: float = 0.7,
    max_tokens: int = 4096,
) -> AsyncGenerator[str, None]:
    """Generate a streaming response using OpenAI-compatible chat API."""
    model = model or runtime_settings.llm_model

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": model,
        "messages": messages,
        "stream": True,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    async with httpx.AsyncClient(timeout=300.0) as client:
        async with client.stream(
            "POST",
            f"{_base_url()}/chat/completions",
            headers=_headers(),
            json=payload,
        ) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if line.startswith("data: "):
                    data_str = line[6:]
                    if data_str.strip() == "[DONE]":
                        break
                    data = json.loads(data_str)
                    choices = data.get("choices", [])
                    if choices:
                        content = choices[0].get("delta", {}).get("content", "")
                        if content:
                            yield content


async def chat(
    messages: list[dict],
    model: str | None = None,
    temperature: float = 0.7,
    max_tokens: int = 4096,
) -> str:
    """Chat completion using OpenAI-compatible API."""
    model = model or runtime_settings.llm_model

    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    async with httpx.AsyncClient(timeout=300.0) as client:
        resp = await client.post(
            f"{_base_url()}/chat/completions",
            headers=_headers(),
            json=payload,
        )
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"].get("content", "")
        return _strip_think(content) if content else ""
