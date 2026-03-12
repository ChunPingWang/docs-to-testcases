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
    ollama_connected: bool
    chroma_connected: bool
    models_available: list[str]
