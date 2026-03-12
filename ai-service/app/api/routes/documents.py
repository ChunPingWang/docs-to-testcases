import uuid

from fastapi import APIRouter, HTTPException, BackgroundTasks

from app.config import settings
from app.models.requests import ProcessDocumentRequest
from app.models.responses import ProcessDocumentResponse
from app.core.document_parser import parse_document
from app.core.chunking.base_chunker import chunk_by_sections, chunk_general
from app.core.embedding.ollama_embedder import embed_texts
from app.core.vectorstore.chroma_store import add_chunks, delete_document_chunks
from app.core.runtime_settings import runtime_settings

router = APIRouter()


async def _process_document(req: ProcessDocumentRequest) -> ProcessDocumentResponse:
    """Internal processing pipeline: parse → chunk → embed → store."""
    # 1. Parse document
    parsed = parse_document(req.file_path, req.file_type)

    # 2. Chunk — choose strategy based on runtime_settings
    sections = parsed.get("sections", [])
    strategy = runtime_settings.chunking_strategy

    if strategy == "table_aware" and sections:
        from app.core.chunking.table_aware_chunker import chunk_table_aware
        chunks = chunk_table_aware(sections)
    elif strategy == "semantic" and sections:
        from app.core.chunking.semantic_chunker import chunk_semantic
        chunks = await chunk_semantic(sections)
    elif sections:
        chunks = chunk_by_sections(sections)
    else:
        chunks = chunk_general(parsed["text"])

    if not chunks:
        return ProcessDocumentResponse(
            document_id=req.document_id,
            status="processed",
            chunk_count=0,
            message="Document parsed but no content found to embed.",
        )

    # 3. Embed
    texts = [c["text"] for c in chunks]
    embeddings = await embed_texts(texts)

    # 4. Store in ChromaDB
    chunk_ids = [f"{req.document_id}_{c['chunk_index']}" for c in chunks]
    metadatas = [
        {
            "document_id": req.document_id,
            "project_id": req.project_id,
            "chunk_index": c["chunk_index"],
            "section_title": c.get("section_title", ""),
            "heading_path": c.get("heading_path", ""),
            "page_number": c.get("page_number") or 0,
            "is_table": c.get("is_table", False),
        }
        for c in chunks
    ]

    add_chunks(
        project_id=req.project_id,
        chunk_ids=chunk_ids,
        embeddings=embeddings,
        documents=texts,
        metadatas=metadatas,
    )

    return ProcessDocumentResponse(
        document_id=req.document_id,
        status="processed",
        chunk_count=len(chunks),
        message=f"Successfully processed {len(chunks)} chunks.",
    )


@router.post("/process", response_model=ProcessDocumentResponse)
async def process_document(req: ProcessDocumentRequest):
    """Parse, chunk, embed, and store a document."""
    try:
        result = await _process_document(req)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"File not found: {req.file_path}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


@router.delete("/{document_id}")
async def delete_document(document_id: str, project_id: str):
    """Remove document embeddings from ChromaDB."""
    try:
        delete_document_chunks(project_id, document_id)
        return {"status": "deleted", "document_id": document_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
