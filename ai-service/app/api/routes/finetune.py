import json
import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException

from app.config import settings
from app.models.requests import PrepareFinetuneRequest, StartFinetuneRequest
from app.core.vectorstore.chroma_store import get_collection
from app.core.llm.ollama_client import generate
from app.core.llm.prompts.training_data_prompt import (
    TRAINING_DATA_SYSTEM,
    QA_PAIR_PROMPT,
    GHERKIN_PAIR_PROMPT,
)

router = APIRouter()

# In-memory job tracking (production would use DB)
_jobs: dict[str, dict] = {}


@router.post("/prepare")
async def prepare_training_data(req: PrepareFinetuneRequest):
    """Generate training data pairs from processed documents."""
    job_id = str(uuid.uuid4())
    _jobs[job_id] = {"status": "preparing_data", "project_id": req.project_id}

    try:
        # Get all documents from ChromaDB
        collection = get_collection(req.project_id)
        all_docs = collection.get(include=["documents", "metadatas"])

        if not all_docs["documents"]:
            raise HTTPException(status_code=404, detail="No documents found for this project.")

        training_pairs = []

        # Generate QA pairs from each chunk
        for i, doc_text in enumerate(all_docs["documents"]):
            if len(doc_text) < 50:
                continue

            try:
                # Generate QA pairs
                qa_response = await generate(
                    prompt=QA_PAIR_PROMPT.format(content=doc_text[:2000]),
                    system=TRAINING_DATA_SYSTEM,
                    temperature=0.5,
                    max_tokens=2048,
                )
                pairs = json.loads(qa_response)
                if isinstance(pairs, list):
                    training_pairs.extend(pairs)
            except (json.JSONDecodeError, Exception):
                continue

            try:
                # Generate Gherkin pairs
                gherkin_response = await generate(
                    prompt=GHERKIN_PAIR_PROMPT.format(content=doc_text[:2000]),
                    system=TRAINING_DATA_SYSTEM,
                    temperature=0.5,
                    max_tokens=2048,
                )
                pair = json.loads(gherkin_response)
                if isinstance(pair, dict):
                    training_pairs.append(pair)
            except (json.JSONDecodeError, Exception):
                continue

        # Save training data
        output_dir = Path(settings.finetune_dir) / req.project_id
        output_dir.mkdir(parents=True, exist_ok=True)

        # Split into train/validation
        split_idx = int(len(training_pairs) * 0.9)
        train_data = training_pairs[:split_idx]
        val_data = training_pairs[split_idx:]

        train_file = output_dir / "train.jsonl"
        val_file = output_dir / "val.jsonl"

        with open(train_file, "w") as f:
            for pair in train_data:
                f.write(json.dumps(pair) + "\n")

        with open(val_file, "w") as f:
            for pair in val_data:
                f.write(json.dumps(pair) + "\n")

        _jobs[job_id] = {
            "status": "data_prepared",
            "project_id": req.project_id,
            "training_pairs": len(training_pairs),
            "train_file": str(train_file),
            "val_file": str(val_file),
        }

        return {
            "job_id": job_id,
            "status": "data_prepared",
            "training_pairs": len(training_pairs),
            "train_samples": len(train_data),
            "val_samples": len(val_data),
        }

    except HTTPException:
        raise
    except Exception as e:
        _jobs[job_id]["status"] = "failed"
        _jobs[job_id]["error"] = str(e)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/start")
async def start_finetune(req: StartFinetuneRequest):
    """Start fine-tuning. Creates an Ollama Modelfile with optimized system prompt."""
    job_id = str(uuid.uuid4())

    try:
        # For Ollama, use Modelfile approach (true fine-tuning requires external tools)
        collection = get_collection(req.project_id)
        all_docs = collection.get(include=["documents"])

        if not all_docs["documents"]:
            raise HTTPException(status_code=404, detail="No documents found.")

        # Build a comprehensive system prompt from documents
        doc_summary = "\n".join(all_docs["documents"][:20])  # Use first 20 chunks

        system_prompt = f"""You are an expert QA engineer specialized in this system. You have deep knowledge of the following system design:

{doc_summary[:4000]}

Use this knowledge to:
1. Answer questions about the system accurately
2. Generate comprehensive Gherkin test cases (positive and negative)
3. Generate executable test code (pytest-bdd and Cucumber.js)
Always reference specific system components and APIs in your responses."""

        # Create Ollama Modelfile
        model_name = f"project-{req.project_id[:8]}-custom"
        modelfile_content = f"""FROM {settings.llm_model}
SYSTEM \"\"\"
{system_prompt}
\"\"\"
PARAMETER temperature 0.3
PARAMETER num_predict 8192
"""

        output_dir = Path(settings.finetune_dir) / req.project_id
        output_dir.mkdir(parents=True, exist_ok=True)
        modelfile_path = output_dir / "Modelfile"

        with open(modelfile_path, "w") as f:
            f.write(modelfile_content)

        _jobs[job_id] = {
            "status": "completed",
            "project_id": req.project_id,
            "model_name": model_name,
            "modelfile_path": str(modelfile_path),
            "note": "Modelfile created. Run 'ollama create' to register the model.",
        }

        return {
            "job_id": job_id,
            "status": "completed",
            "model_name": model_name,
            "modelfile_path": str(modelfile_path),
            "message": f"Modelfile created at {modelfile_path}. "
            f"To register: ollama create {model_name} -f {modelfile_path}",
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{job_id}/status")
async def get_finetune_status(job_id: str):
    """Get fine-tuning job status."""
    job = _jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    return job
