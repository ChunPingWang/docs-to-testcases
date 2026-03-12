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
