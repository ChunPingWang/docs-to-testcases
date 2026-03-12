"""Ragas RAG evaluation endpoint."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.rag.evaluation import evaluate_rag, EvalSample

router = APIRouter()


class EvalSampleRequest(BaseModel):
    question: str
    answer: str
    contexts: list[str]
    ground_truth: str = ""


class EvaluateRequest(BaseModel):
    samples: list[EvalSampleRequest]


class EvaluateResponse(BaseModel):
    scores: dict | None = None
    sample_count: int = 0
    error: str | None = None


@router.post("/evaluate", response_model=EvaluateResponse)
async def evaluate_endpoint(req: EvaluateRequest):
    """Evaluate RAG pipeline quality using Ragas metrics.

    Expects a list of samples, each with question, answer, contexts,
    and optionally ground_truth. Returns faithfulness, answer_relevancy,
    context_precision, and context_recall scores.
    """
    if not req.samples:
        raise HTTPException(status_code=400, detail="No samples provided")

    samples = [
        EvalSample(
            question=s.question,
            answer=s.answer,
            contexts=s.contexts,
            ground_truth=s.ground_truth,
        )
        for s in req.samples
    ]

    result = await evaluate_rag(samples)

    if "error" in result and result["error"]:
        return EvaluateResponse(error=result["error"], sample_count=len(samples))

    return EvaluateResponse(
        scores=result.get("scores"),
        sample_count=result.get("sample_count", len(samples)),
    )
