from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # ── Primary / default provider (backward-compatible) ────
    llm_api_base_url: str = "https://generativelanguage.googleapis.com/v1beta/openai"
    llm_api_key: str = ""
    llm_model: str = "gemini-2.5-flash"
    embedding_model: str = "gemini-embedding-001"

    # ── Optional additional providers (set via env) ─────────
    # Ollama (local)
    ollama_api_base_url: str = "http://ollama:11434/v1"
    ollama_api_key: str = "ollama"
    ollama_llm_model: str = "llama3:8b"
    ollama_embedding_model: str = "nomic-embed-text"
    ollama_enabled: bool = False
    ollama_optimization_mode: str = "rag_finetune"

    # OpenAI
    openai_api_base_url: str = "https://api.openai.com/v1"
    openai_api_key: str = ""
    openai_llm_model: str = "gpt-4o"
    openai_embedding_model: str = "text-embedding-3-small"
    openai_enabled: bool = False
    openai_optimization_mode: str = "rag"

    # ── Infrastructure ──────────────────────────────────────
    chroma_host: str = "chromadb"
    chroma_port: int = 8000

    upload_dir: str = "/data/uploads"
    features_dir: str = "/data/features"
    generated_tests_dir: str = "/data/generated-tests"
    finetune_dir: str = "/data/finetune"

    chunk_size: int = 1000
    chunk_overlap: int = 200
    retrieval_top_k: int = 10

    class Config:
        env_file = ".env"


settings = Settings()


def init_provider_registry() -> None:
    """Register all enabled providers into the global registry.

    Called once at application startup.
    """
    from app.core.llm.provider_registry import ProviderConfig, provider_registry

    # 1. Primary provider (always registered)
    provider_registry.register(
        ProviderConfig(
            name="gemini",
            base_url=settings.llm_api_base_url,
            api_key=settings.llm_api_key,
            llm_model=settings.llm_model,
            embedding_model=settings.embedding_model,
            supports_finetune=False,
            optimization_mode="rag",
        )
    )

    # 2. Ollama (local)
    if settings.ollama_enabled:
        provider_registry.register(
            ProviderConfig(
                name="ollama",
                base_url=settings.ollama_api_base_url,
                api_key=settings.ollama_api_key,
                llm_model=settings.ollama_llm_model,
                embedding_model=settings.ollama_embedding_model,
                supports_finetune=True,
                optimization_mode=settings.ollama_optimization_mode,
            )
        )

    # 3. OpenAI
    if settings.openai_enabled:
        provider_registry.register(
            ProviderConfig(
                name="openai",
                base_url=settings.openai_api_base_url,
                api_key=settings.openai_api_key,
                llm_model=settings.openai_llm_model,
                embedding_model=settings.openai_embedding_model,
                supports_finetune=True,
                optimization_mode=settings.openai_optimization_mode,
            )
        )
