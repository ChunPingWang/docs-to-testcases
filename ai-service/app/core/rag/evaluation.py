"""Ragas-based RAG evaluation pipeline."""

import logging
from dataclasses import dataclass

from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall,
)
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper
from datasets import Dataset
from langchain_openai import ChatOpenAI

from app.config import settings
from app.core.runtime_settings import runtime_settings
from app.core.rag.eval_embeddings import MiniMaxEmbeddings

logger = logging.getLogger(__name__)


@dataclass
class EvalSample:
    """A single evaluation sample."""
    question: str
    answer: str
    contexts: list[str]
    ground_truth: str = ""


def _build_llm():
    """Build a LangChain ChatOpenAI pointing at the active provider."""
    from app.core.llm.provider_registry import provider_registry
    provider = provider_registry.get_active()
    base_url = provider.base_url if provider else settings.llm_api_base_url
    api_key = provider.api_key if provider else settings.llm_api_key

    return ChatOpenAI(
        model=runtime_settings.llm_model,
        openai_api_key=api_key,
        openai_api_base=base_url,
        temperature=0.0,
        max_tokens=2048,
    )


def _build_embeddings():
    """Build a LangChain Embeddings adapter for MiniMax."""
    return MiniMaxEmbeddings()


async def evaluate_rag(samples: list[EvalSample]) -> dict:
    """Run Ragas evaluation on a list of samples.

    Args:
        samples: List of EvalSample with question, answer, contexts, and ground_truth.

    Returns:
        Dict with metric scores: faithfulness, answer_relevancy,
        context_precision, context_recall, and per-sample details.
    """
    if not samples:
        return {"error": "No samples provided"}

    # Build dataset
    data = {
        "question": [s.question for s in samples],
        "answer": [s.answer for s in samples],
        "contexts": [s.contexts for s in samples],
        "ground_truth": [s.ground_truth for s in samples],
    }
    dataset = Dataset.from_dict(data)

    # Select metrics — context_recall requires ground_truth
    metrics = [faithfulness, answer_relevancy, context_precision]
    has_ground_truth = any(s.ground_truth.strip() for s in samples)
    if has_ground_truth:
        metrics.append(context_recall)

    llm = LangchainLLMWrapper(_build_llm())
    embeddings = LangchainEmbeddingsWrapper(_build_embeddings())

    try:
        result = evaluate(
            dataset=dataset,
            metrics=metrics,
            llm=llm,
            embeddings=embeddings,
        )

        scores = {k: v for k, v in result.items() if isinstance(v, (int, float))}
        return {
            "scores": scores,
            "sample_count": len(samples),
        }
    except Exception as e:
        logger.error(f"Ragas evaluation failed: {e}")
        return {"error": str(e)}
