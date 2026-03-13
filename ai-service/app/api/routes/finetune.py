"""Fine-tuning / optimization API — provider-aware strategy dispatcher.

Depending on the active provider's optimization_mode, the /start endpoint
will execute a different strategy:

  rag            → no-op (RAG-only, no model customization needed)
  rag_finetune   → create Ollama Modelfile with LoRA adapter placeholder
  rag_fewshot    → index approved examples into ChromaDB for dynamic few-shot
  prompt_only    → generate an Ollama Modelfile with a rich system prompt
"""

import json
import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException

from app.config import settings
from app.core.runtime_settings import runtime_settings
from app.core.llm.provider_registry import provider_registry
from app.models.requests import PrepareFinetuneRequest, StartFinetuneRequest
from app.core.vectorstore.chroma_store import get_collection, add_chunks
from app.core.llm.ollama_client import generate
from app.core.llm.prompts.training_data_prompt import (
    TRAINING_DATA_SYSTEM,
    QA_PAIR_PROMPT,
    GHERKIN_PAIR_PROMPT,
)

router = APIRouter()

# In-memory job tracking (production would use DB)
_jobs: dict[str, dict] = {}


# ── Shared: prepare training data (unchanged) ──────────────


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
                qa_response = await generate(
                    prompt=QA_PAIR_PROMPT.format(content=doc_text[:2000]),
                    system=TRAINING_DATA_SYSTEM,
                    temperature=runtime_settings.temperature_finetune,
                    max_tokens=runtime_settings.max_tokens_finetune,
                )
                pairs = json.loads(qa_response)
                if isinstance(pairs, list):
                    training_pairs.extend(pairs)
            except (json.JSONDecodeError, Exception):
                continue

            try:
                gherkin_response = await generate(
                    prompt=GHERKIN_PAIR_PROMPT.format(content=doc_text[:2000]),
                    system=TRAINING_DATA_SYSTEM,
                    temperature=runtime_settings.temperature_finetune,
                    max_tokens=runtime_settings.max_tokens_finetune,
                )
                pair = json.loads(gherkin_response)
                if isinstance(pair, dict):
                    training_pairs.append(pair)
            except (json.JSONDecodeError, Exception):
                continue

        # Save training data
        output_dir = Path(settings.finetune_dir) / req.project_id
        output_dir.mkdir(parents=True, exist_ok=True)

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


# ── Strategy dispatcher ────────────────────────────────────


@router.post("/start")
async def start_finetune(req: StartFinetuneRequest):
    """Start optimization using the strategy dictated by the active provider.

    Returns different payloads depending on optimization_mode:
      - rag            → message only (nothing extra to do)
      - rag_finetune   → Modelfile + instructions for ollama create
      - rag_fewshot    → stores approved examples in ChromaDB
      - prompt_only    → generates Modelfile with rich system prompt
    """
    mode = provider_registry.active_optimization_mode
    provider = provider_registry.get_active()
    provider_name = provider.name if provider else "unknown"

    if mode == "rag":
        return _strategy_rag_only(req, provider_name)
    elif mode == "rag_finetune":
        return await _strategy_rag_finetune(req, provider_name)
    elif mode == "rag_fewshot":
        return await _strategy_rag_fewshot(req, provider_name)
    elif mode == "prompt_only":
        return await _strategy_prompt_only(req, provider_name)
    else:
        raise HTTPException(status_code=400, detail=f"Unknown optimization_mode: {mode}")


# ── Individual strategies ──────────────────────────────────


def _strategy_rag_only(req: StartFinetuneRequest, provider_name: str) -> dict:
    """Cloud providers (Gemini, OpenAI) — RAG is sufficient."""
    return {
        "job_id": str(uuid.uuid4()),
        "status": "completed",
        "provider": provider_name,
        "optimization_mode": "rag",
        "message": (
            "RAG-only mode: no model fine-tuning is performed. "
            "The system retrieves relevant document chunks at query time and injects "
            "them into the prompt. Upload more documents to improve quality."
        ),
    }


async def _strategy_rag_finetune(req: StartFinetuneRequest, provider_name: str) -> dict:
    """Local Ollama with GPU — generate Modelfile for LoRA fine-tuning."""
    job_id = str(uuid.uuid4())

    collection = get_collection(req.project_id)
    all_docs = collection.get(include=["documents"])
    if not all_docs["documents"]:
        raise HTTPException(status_code=404, detail="No documents found.")

    train_file = Path(settings.finetune_dir) / req.project_id / "train.jsonl"
    if not train_file.exists():
        raise HTTPException(
            status_code=400,
            detail="Training data not found. Call POST /ai/finetune/prepare first.",
        )

    provider = provider_registry.get_active()
    base_model = provider.llm_model if provider else runtime_settings.llm_model

    doc_summary = "\n".join(all_docs["documents"][:20])
    system_prompt = _build_system_prompt(doc_summary)

    model_name = f"project-{req.project_id[:8]}-custom"
    modelfile_content = (
        f"FROM {base_model}\n"
        f'SYSTEM """\n{system_prompt}\n"""\n'
        f"PARAMETER temperature 0.3\n"
        f"PARAMETER num_predict 8192\n"
        f"# To add LoRA adapter after training:\n"
        f"# ADAPTER /path/to/lora-adapter\n"
    )

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
        "train_file": str(train_file),
    }

    return {
        "job_id": job_id,
        "status": "completed",
        "provider": provider_name,
        "optimization_mode": "rag_finetune",
        "model_name": model_name,
        "modelfile_path": str(modelfile_path),
        "train_file": str(train_file),
        "message": (
            f"Modelfile created at {modelfile_path}. "
            f"Training data at {train_file}. "
            f"To register: ollama create {model_name} -f {modelfile_path}"
        ),
    }


async def _strategy_rag_fewshot(req: StartFinetuneRequest, provider_name: str) -> dict:
    """Index approved training pairs into ChromaDB as few-shot examples."""
    job_id = str(uuid.uuid4())

    train_file = Path(settings.finetune_dir) / req.project_id / "train.jsonl"
    if not train_file.exists():
        raise HTTPException(
            status_code=400,
            detail="Training data not found. Call POST /ai/finetune/prepare first.",
        )

    pairs = []
    with open(train_file) as f:
        for line in f:
            line = line.strip()
            if line:
                pairs.append(json.loads(line))

    if not pairs:
        raise HTTPException(status_code=400, detail="Training file is empty.")

    from app.core.embedding.ollama_embedder import embed_texts

    texts = []
    metadatas = []
    chunk_ids = []

    for i, pair in enumerate(pairs):
        instruction = pair.get("instruction", "")
        inp = pair.get("input", "")
        output = pair.get("output", "")
        combined = f"[Instruction] {instruction}\n[Input] {inp}\n[Output] {output}"

        texts.append(combined)
        metadatas.append({
            "document_id": f"fewshot_{req.project_id}",
            "project_id": req.project_id,
            "chunk_index": i,
            "doc_type": "approved_example",
            "section_title": instruction[:100],
            "heading_path": "",
            "page_number": 0,
            "is_table": False,
        })
        chunk_ids.append(f"fewshot_{req.project_id}_{i}")

    embeddings = await embed_texts(texts)
    add_chunks(
        project_id=req.project_id,
        chunk_ids=chunk_ids,
        embeddings=embeddings,
        documents=texts,
        metadatas=metadatas,
    )

    _jobs[job_id] = {
        "status": "completed",
        "project_id": req.project_id,
        "examples_indexed": len(pairs),
    }

    return {
        "job_id": job_id,
        "status": "completed",
        "provider": provider_name,
        "optimization_mode": "rag_fewshot",
        "examples_indexed": len(pairs),
        "message": (
            f"Indexed {len(pairs)} approved examples into ChromaDB. "
            "They will be retrieved as few-shot context during generation."
        ),
    }


async def _strategy_prompt_only(req: StartFinetuneRequest, provider_name: str) -> dict:
    """Ollama without GPU — Modelfile with rich system prompt only."""
    job_id = str(uuid.uuid4())

    collection = get_collection(req.project_id)
    all_docs = collection.get(include=["documents"])
    if not all_docs["documents"]:
        raise HTTPException(status_code=404, detail="No documents found.")

    provider = provider_registry.get_active()
    base_model = provider.llm_model if provider else runtime_settings.llm_model

    doc_summary = "\n".join(all_docs["documents"][:20])
    system_prompt = _build_system_prompt(doc_summary)

    model_name = f"project-{req.project_id[:8]}-custom"
    modelfile_content = (
        f"FROM {base_model}\n"
        f'SYSTEM """\n{system_prompt}\n"""\n'
        f"PARAMETER temperature 0.3\n"
        f"PARAMETER num_predict 8192\n"
    )

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
    }

    return {
        "job_id": job_id,
        "status": "completed",
        "provider": provider_name,
        "optimization_mode": "prompt_only",
        "model_name": model_name,
        "modelfile_path": str(modelfile_path),
        "message": (
            f"Modelfile created at {modelfile_path}. "
            f"To register: ollama create {model_name} -f {modelfile_path}"
        ),
    }


# ── Helpers ────────────────────────────────────────────────


def _build_system_prompt(doc_summary: str) -> str:
    return (
        "You are an expert QA engineer specialized in this system. "
        "You have deep knowledge of the following system design:\n\n"
        f"{doc_summary[:4000]}\n\n"
        "Use this knowledge to:\n"
        "1. Answer questions about the system accurately\n"
        "2. Generate comprehensive Gherkin test cases (positive and negative)\n"
        "3. Generate executable test code (pytest-bdd and Cucumber.js)\n"
        "Always reference specific system components and APIs in your responses."
    )


@router.get("/{job_id}/status")
async def get_finetune_status(job_id: str):
    """Get fine-tuning job status."""
    job = _jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    return job
