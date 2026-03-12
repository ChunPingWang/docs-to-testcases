"""Mutable in-memory runtime settings, initialized from env-based config."""

from app.config import settings as _static


class RuntimeSettings:
    """Singleton holding runtime-adjustable parameters."""

    def __init__(self):
        self.reset()

    # ── Query / Mutate ────────────────────────────────────

    def to_dict(self) -> dict:
        return {
            "llm_model": self.llm_model,
            "embedding_model": self.embedding_model,
            "temperature_qa": self.temperature_qa,
            "temperature_test_case": self.temperature_test_case,
            "temperature_test_code": self.temperature_test_code,
            "temperature_finetune": self.temperature_finetune,
            "max_tokens_qa": self.max_tokens_qa,
            "max_tokens_test_case": self.max_tokens_test_case,
            "max_tokens_test_code": self.max_tokens_test_code,
            "max_tokens_finetune": self.max_tokens_finetune,
            "chunk_size": self.chunk_size,
            "chunk_overlap": self.chunk_overlap,
            "retrieval_top_k": self.retrieval_top_k,
            "min_relevance_score": self.min_relevance_score,
            "use_reranker": self.use_reranker,
            "reranker_initial_k": self.reranker_initial_k,
            "chunking_strategy": self.chunking_strategy,
            "semantic_chunk_threshold": self.semantic_chunk_threshold,
        }

    def update(self, data: dict) -> dict:
        """Partial update — only keys present in *data* are changed."""
        valid_keys = set(self.to_dict().keys())
        for key, value in data.items():
            if key in valid_keys and value is not None:
                setattr(self, key, value)
        return self.to_dict()

    def reset(self):
        """Reset every field to its default (from env / config.py)."""
        self.llm_model: str = _static.llm_model  # e.g. MiniMax-M2.5
        self.embedding_model: str = _static.embedding_model  # e.g. embo-01

        # Temperature defaults per operation type
        self.temperature_qa: float = 0.7
        self.temperature_test_case: float = 0.3
        self.temperature_test_code: float = 0.2
        self.temperature_finetune: float = 0.5

        # Max tokens defaults per operation type
        self.max_tokens_qa: int = 4096
        self.max_tokens_test_case: int = 8192
        self.max_tokens_test_code: int = 8192
        self.max_tokens_finetune: int = 2048

        # RAG parameters
        self.chunk_size: int = _static.chunk_size
        self.chunk_overlap: int = _static.chunk_overlap
        self.retrieval_top_k: int = _static.retrieval_top_k
        self.min_relevance_score: float = 0.3
        self.use_reranker: bool = False
        self.reranker_initial_k: int = 30
        self.chunking_strategy: str = "fixed"  # "fixed" | "table_aware" | "semantic"
        self.semantic_chunk_threshold: float = 0.5


runtime_settings = RuntimeSettings()
