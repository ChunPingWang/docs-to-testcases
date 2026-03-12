from collections.abc import AsyncGenerator

from app.core.rag.retriever import retrieve_context, format_context
from app.core.llm.ollama_client import generate, generate_stream


QA_SYSTEM_PROMPT = """You are a knowledgeable assistant that answers questions about system design documents.
Use the provided context to answer questions accurately. If the context doesn't contain enough information
to answer the question, say so clearly. Always reference specific parts of the documentation when possible."""

QA_PROMPT_TEMPLATE = """Context from the system design documents:

{context}

Question: {question}

Provide a clear, detailed answer based on the context above."""


async def qa_answer(
    project_id: str,
    question: str,
    model: str | None = None,
) -> dict:
    """Answer a question using RAG (non-streaming)."""
    chunks = await retrieve_context(project_id, question)
    context = format_context(chunks)

    prompt = QA_PROMPT_TEMPLATE.format(context=context, question=question)
    answer = await generate(prompt, system=QA_SYSTEM_PROMPT, model=model)

    return {
        "answer": answer,
        "context_chunks": [
            {
                "text": c["text"][:200],
                "metadata": c["metadata"],
                "relevance_score": c["relevance_score"],
            }
            for c in chunks
        ],
    }


async def qa_answer_stream(
    project_id: str,
    question: str,
    model: str | None = None,
) -> AsyncGenerator[str, None]:
    """Answer a question using RAG (streaming)."""
    chunks = await retrieve_context(project_id, question)
    context = format_context(chunks)

    prompt = QA_PROMPT_TEMPLATE.format(context=context, question=question)

    async for token in generate_stream(prompt, system=QA_SYSTEM_PROMPT, model=model):
        yield token
