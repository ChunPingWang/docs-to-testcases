"""Model provider registry — central configuration for multi-provider support.

Each provider defines:
  - connection info (base_url, api_key)
  - available models (llm + embedding)
  - capabilities (supports_finetune, supports_streaming, etc.)
  - optimization_mode: how the system should optimise generation for this provider

Optimization modes:
  - "rag"            → retrieval-augmented generation only (all cloud providers)
  - "rag_finetune"   → RAG + LoRA/QLoRA fine-tuning (local Ollama with GPU)
  - "rag_fewshot"    → RAG + dynamic few-shot examples from approved history
  - "prompt_only"    → system-prompt injection via Modelfile (Ollama, no GPU)
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field


# ── Data classes ────────────────────────────────────────────


@dataclass
class ProviderConfig:
    """Immutable-ish description of a single model provider."""

    name: str
    base_url: str
    api_key: str = ""

    # Models offered by this provider
    llm_model: str = ""
    embedding_model: str = ""

    # Capability flags
    supports_streaming: bool = True
    supports_finetune: bool = False
    supports_embedding: bool = True

    # How to optimise when this provider is active
    optimization_mode: str = "rag"  # rag | rag_finetune | rag_fewshot | prompt_only

    # Provider-specific extra headers / params
    extra_headers: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "base_url": self.base_url,
            "api_key_set": bool(self.api_key),  # never expose raw key
            "llm_model": self.llm_model,
            "embedding_model": self.embedding_model,
            "supports_streaming": self.supports_streaming,
            "supports_finetune": self.supports_finetune,
            "supports_embedding": self.supports_embedding,
            "optimization_mode": self.optimization_mode,
        }


# ── Registry singleton ─────────────────────────────────────


class ProviderRegistry:
    """Thread-safe registry of all configured providers."""

    VALID_OPTIMIZATION_MODES = {"rag", "rag_finetune", "rag_fewshot", "prompt_only"}

    def __init__(self):
        self._providers: dict[str, ProviderConfig] = {}
        self._active: str = ""

    # ── CRUD ────────────────────────────────────────────────

    def register(self, provider: ProviderConfig) -> None:
        self._providers[provider.name] = provider
        # First registered provider becomes active by default
        if not self._active:
            self._active = provider.name

    def unregister(self, name: str) -> bool:
        if name not in self._providers:
            return False
        del self._providers[name]
        if self._active == name:
            self._active = next(iter(self._providers), "")
        return True

    def update(self, name: str, data: dict) -> ProviderConfig | None:
        """Partial update of an existing provider."""
        provider = self._providers.get(name)
        if provider is None:
            return None
        for key, value in data.items():
            if value is not None and hasattr(provider, key) and key != "name":
                setattr(provider, key, value)
        return provider

    # ── Query ───────────────────────────────────────────────

    def get(self, name: str) -> ProviderConfig | None:
        return self._providers.get(name)

    def get_active(self) -> ProviderConfig | None:
        return self._providers.get(self._active)

    @property
    def active_name(self) -> str:
        return self._active

    def set_active(self, name: str) -> bool:
        if name not in self._providers:
            return False
        self._active = name
        return True

    def list_all(self) -> list[ProviderConfig]:
        return list(self._providers.values())

    def list_names(self) -> list[str]:
        return list(self._providers.keys())

    # ── Convenience ─────────────────────────────────────────

    @property
    def active_base_url(self) -> str:
        p = self.get_active()
        return p.base_url if p else ""

    @property
    def active_api_key(self) -> str:
        p = self.get_active()
        return p.api_key if p else ""

    @property
    def active_llm_model(self) -> str:
        p = self.get_active()
        return p.llm_model if p else ""

    @property
    def active_embedding_model(self) -> str:
        p = self.get_active()
        return p.embedding_model if p else ""

    @property
    def active_optimization_mode(self) -> str:
        p = self.get_active()
        return p.optimization_mode if p else "rag"

    @property
    def active_extra_headers(self) -> dict:
        p = self.get_active()
        return copy.deepcopy(p.extra_headers) if p else {}

    def to_dict(self) -> dict:
        return {
            "active_provider": self._active,
            "providers": {n: p.to_dict() for n, p in self._providers.items()},
        }


# ── Module-level singleton ──────────────────────────────────

provider_registry = ProviderRegistry()
