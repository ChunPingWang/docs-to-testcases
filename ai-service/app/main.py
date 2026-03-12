from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import documents, qa, generation, finetune, health

app = FastAPI(
    title="Docs-to-TestCases AI Service",
    version="1.0.0",
    docs_url="/ai/docs",
    openapi_url="/ai/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/ai", tags=["health"])
app.include_router(documents.router, prefix="/ai/documents", tags=["documents"])
app.include_router(qa.router, prefix="/ai/qa", tags=["qa"])
app.include_router(generation.router, prefix="/ai/generate", tags=["generation"])
app.include_router(finetune.router, prefix="/ai/finetune", tags=["finetune"])
