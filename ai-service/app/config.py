from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    llm_api_base_url: str = "https://api.minimax.io/v1"
    llm_api_key: str = ""
    llm_model: str = "MiniMax-M2.5"
    embedding_model: str = "embo-01"

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
