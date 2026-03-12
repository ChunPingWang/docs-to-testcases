import json

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.models.requests import AskQuestionRequest
from app.core.rag.chain import qa_answer, qa_answer_stream

router = APIRouter()


@router.post("/ask")
async def ask_question(req: AskQuestionRequest):
    """Ask a question with RAG — returns SSE stream."""

    async def event_generator():
        async for token in qa_answer_stream(
            project_id=req.project_id,
            question=req.question,
            model=req.model_name,
        ):
            yield f"data: {json.dumps({'token': token})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/ask/sync")
async def ask_question_sync(req: AskQuestionRequest):
    """Ask a question with RAG — returns full response (non-streaming)."""
    result = await qa_answer(
        project_id=req.project_id,
        question=req.question,
        model=req.model_name,
    )
    return result
