from pydantic import BaseModel


class ProcessDocumentRequest(BaseModel):
    document_id: str
    file_path: str
    file_type: str
    project_id: str


class AskQuestionRequest(BaseModel):
    project_id: str
    question: str
    model_name: str | None = None


class GenerateTestCasesRequest(BaseModel):
    project_id: str
    document_id: str | None = None
    feature_description: str | None = None
    include_positive: bool = True
    include_negative: bool = True
    include_api_tests: bool = True
    include_e2e_tests: bool = True


class GenerateTestCodeRequest(BaseModel):
    gherkin_content: str
    language: str  # "python" or "javascript"
    project_id: str
    context_query: str | None = None


class PrepareFinetuneRequest(BaseModel):
    project_id: str


class StartFinetuneRequest(BaseModel):
    project_id: str
    config: dict = {}


class UpdateSettingsRequest(BaseModel):
    llm_model: str | None = None
    embedding_model: str | None = None
    temperature_qa: float | None = None
    temperature_test_case: float | None = None
    temperature_test_code: float | None = None
    temperature_finetune: float | None = None
    max_tokens_qa: int | None = None
    max_tokens_test_case: int | None = None
    max_tokens_test_code: int | None = None
    max_tokens_finetune: int | None = None
    chunk_size: int | None = None
    chunk_overlap: int | None = None
    retrieval_top_k: int | None = None
