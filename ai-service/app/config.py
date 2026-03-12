from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    ollama_base_url: str = "http://10.0.0.4:11434"
    llm_model: str = "llama3.1:70b"
    embedding_model: str = "nomic-embed-text"

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
