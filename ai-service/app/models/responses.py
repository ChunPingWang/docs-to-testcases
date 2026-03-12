from pydantic import BaseModel


class ProcessDocumentResponse(BaseModel):
    document_id: str
    status: str
    chunk_count: int
    message: str


class GeneratedFeature(BaseModel):
    name: str
    gherkin_content: str
    tags: list[str]
    scenario_count: int


class GenerateTestCasesResponse(BaseModel):
    features: list[GeneratedFeature]
    total_scenarios: int
    message: str


class GeneratedCodeFile(BaseModel):
    filename: str
    content: str
    file_type: str  # "test", "step_def", "conftest", "support"


class GenerateTestCodeResponse(BaseModel):
    language: str
    framework: str
    files: list[GeneratedCodeFile]
    message: str


class HealthResponse(BaseModel):
    status: str
    llm_api_connected: bool
    chroma_connected: bool
    models_available: list[str]


class SettingsResponse(BaseModel):
    llm_model: str
    embedding_model: str
    temperature_qa: float
    temperature_test_case: float
    temperature_test_code: float
    temperature_finetune: float
    max_tokens_qa: int
    max_tokens_test_case: int
    max_tokens_test_code: int
    max_tokens_finetune: int
    chunk_size: int
    chunk_overlap: int
    retrieval_top_k: int
    min_relevance_score: float
    use_reranker: bool
    reranker_initial_k: int
    chunking_strategy: str
    semantic_chunk_threshold: float
