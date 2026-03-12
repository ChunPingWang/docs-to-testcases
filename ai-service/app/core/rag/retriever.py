from app.core.embedding.ollama_embedder import embed_single
from app.core.vectorstore.chroma_store import query_chunks
from app.core.runtime_settings import runtime_settings


async def retrieve_context(
    project_id: str,
    query: str,
    top_k: int = 0,
    document_id: str | None = None,
) -> list[dict]:
    """Retrieve relevant document chunks for a query using RAG."""
    top_k = top_k or runtime_settings.retrieval_top_k
    query_embedding = await embed_single(query)

    where = None
    if document_id:
        where = {"document_id": document_id}

    results = query_chunks(
        project_id=project_id,
        query_embedding=query_embedding,
        n_results=top_k,
        where=where,
    )

    chunks = []
    if results and results["documents"] and results["documents"][0]:
        for i, doc in enumerate(results["documents"][0]):
            metadata = results["metadatas"][0][i] if results["metadatas"] else {}
            distance = results["distances"][0][i] if results["distances"] else 0
            chunks.append({
                "text": doc,
                "metadata": metadata,
                "relevance_score": 1 - distance,  # Convert distance to similarity
            })

    # Sort by relevance (highest first)
    chunks.sort(key=lambda c: c["relevance_score"], reverse=True)

    return chunks


def format_context(chunks: list[dict], max_tokens: int = 4000) -> str:
    """Format retrieved chunks into a context string for the LLM prompt."""
    context_parts = []
    total_length = 0

    for chunk in chunks:
        text = chunk["text"]
        metadata = chunk["metadata"]
        section = metadata.get("section_title", "")
        heading = metadata.get("heading_path", "")

        prefix = ""
        if heading:
            prefix = f"[Section: {heading}]\n"
        elif section:
            prefix = f"[Section: {section}]\n"

        entry = f"{prefix}{text}\n---"

        # Rough token estimate: 1 token ≈ 4 chars
        if total_length + len(entry) / 4 > max_tokens:
            break

        context_parts.append(entry)
        total_length += len(entry) / 4

    return "\n\n".join(context_parts)
