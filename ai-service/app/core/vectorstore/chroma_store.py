from __future__ import annotations

import chromadb
from chromadb.config import Settings as ChromaSettings

from app.config import settings

_client: chromadb.HttpClient | None = None


def get_chroma_client() -> chromadb.HttpClient:
    global _client
    if _client is None:
        _client = chromadb.HttpClient(
            host=settings.chroma_host,
            port=settings.chroma_port,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
    return _client


def get_collection(project_id: str):
    """Get or create a ChromaDB collection for a project."""
    client = get_chroma_client()
    return client.get_or_create_collection(
        name=f"project_{project_id}",
        metadata={"hnsw:space": "cosine"},
    )


def add_chunks(
    project_id: str,
    chunk_ids: list[str],
    embeddings: list[list[float]],
    documents: list[str],
    metadatas: list[dict],
):
    """Add document chunks to the vector store."""
    collection = get_collection(project_id)
    collection.add(
        ids=chunk_ids,
        embeddings=embeddings,
        documents=documents,
        metadatas=metadatas,
    )


def query_chunks(
    project_id: str,
    query_embedding: list[float],
    n_results: int = 10,
    where: dict | None = None,
) -> dict:
    """Query the vector store for similar chunks."""
    collection = get_collection(project_id)
    kwargs = {
        "query_embeddings": [query_embedding],
        "n_results": n_results,
        "include": ["documents", "metadatas", "distances"],
    }
    if where:
        kwargs["where"] = where
    return collection.query(**kwargs)


def delete_document_chunks(project_id: str, document_id: str):
    """Delete all chunks for a specific document from the vector store."""
    collection = get_collection(project_id)
    collection.delete(where={"document_id": document_id})


def delete_collection(project_id: str):
    """Delete an entire project collection."""
    client = get_chroma_client()
    try:
        client.delete_collection(f"project_{project_id}")
    except Exception:
        pass
