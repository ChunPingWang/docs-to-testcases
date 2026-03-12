"""LLM-based pointwise reranker for two-stage retrieval."""

import asyncio
import json
import logging

from app.core.llm.ollama_client import generate

logger = logging.getLogger(__name__)

RERANK_PROMPT_TEMPLATE = """你是一個相關性評分器。請評估以下文件片段與查詢的相關程度。

查詢: {query}

文件片段:
{chunk_text}

請以 JSON 格式回覆，包含 score（0.0 到 1.0）和 reason（簡短說明）：
{{"score": 0.0, "reason": "..."}}

評分標準：
- 1.0：片段直接且完整地回答了查詢
- 0.7-0.9：片段高度相關，包含大部分所需資訊
- 0.4-0.6：片段部分相關，包含一些有用資訊
- 0.1-0.3：片段略微相關，僅有間接關聯
- 0.0：片段完全不相關

只回覆 JSON，不要有其他文字。"""


async def _score_chunk(
    query: str,
    chunk: dict,
    semaphore: asyncio.Semaphore,
) -> dict:
    """Score a single chunk using LLM. Falls back to embedding score on failure."""
    async with semaphore:
        try:
            prompt = RERANK_PROMPT_TEMPLATE.format(
                query=query,
                chunk_text=chunk["text"][:2000],  # Limit chunk text length
            )
            response = await generate(
                prompt=prompt,
                temperature=0.0,
                max_tokens=256,
            )

            # Parse JSON response
            # Try to extract JSON from potential markdown code blocks
            text = response.strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[-1].rsplit("```", 1)[0].strip()

            data = json.loads(text)
            rerank_score = float(data.get("score", 0.0))
            rerank_score = max(0.0, min(1.0, rerank_score))

            return {
                **chunk,
                "rerank_score": rerank_score,
                "rerank_reason": data.get("reason", ""),
            }
        except Exception as e:
            logger.warning(f"Reranker failed for chunk, using embedding score: {e}")
            return {
                **chunk,
                "rerank_score": chunk.get("relevance_score", 0.0),
                "rerank_reason": "fallback to embedding score",
            }


async def rerank_chunks(
    query: str,
    chunks: list[dict],
    top_k: int = 10,
) -> list[dict]:
    """Rerank chunks using LLM pointwise scoring.

    Args:
        query: The user query.
        chunks: Candidate chunks from initial retrieval.
        top_k: Number of top chunks to return after reranking.

    Returns:
        Top-k chunks sorted by rerank_score.
    """
    if not chunks:
        return []

    semaphore = asyncio.Semaphore(5)

    tasks = [_score_chunk(query, chunk, semaphore) for chunk in chunks]
    scored_chunks = await asyncio.gather(*tasks)

    # Sort by rerank score (highest first)
    scored_chunks.sort(key=lambda c: c["rerank_score"], reverse=True)

    return scored_chunks[:top_k]
