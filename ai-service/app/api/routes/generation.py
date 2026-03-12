import re

from fastapi import APIRouter, HTTPException

from app.models.requests import GenerateTestCasesRequest, GenerateTestCodeRequest
from app.models.responses import (
    GenerateTestCasesResponse,
    GeneratedFeature,
    GenerateTestCodeResponse,
    GeneratedCodeFile,
)
from app.core.rag.retriever import retrieve_context, format_context
from app.core.llm.ollama_client import generate
from app.core.llm.prompts.test_case_generation import (
    SYSTEM_PROMPT as TC_SYSTEM,
    build_generation_prompt,
)
from app.core.llm.prompts.test_code_generation import build_code_generation_prompt
from app.utils.gherkin_validator import validate_gherkin, extract_feature_name, split_features

router = APIRouter()


@router.post("/test-cases", response_model=GenerateTestCasesResponse)
async def generate_test_cases(req: GenerateTestCasesRequest):
    """Generate Gherkin test cases using RAG + LLM."""
    # Retrieve context
    query = req.feature_description or "system features, API endpoints, and workflows"
    chunks = await retrieve_context(
        project_id=req.project_id,
        query=query,
        document_id=req.document_id,
        top_k=15,
    )

    if not chunks:
        raise HTTPException(
            status_code=404,
            detail="No document content found. Please upload and process documents first.",
        )

    context = format_context(chunks, max_tokens=4000)

    # Build prompt
    prompt = build_generation_prompt(
        context=context,
        feature_description=req.feature_description,
        include_positive=req.include_positive,
        include_negative=req.include_negative,
        include_api_tests=req.include_api_tests,
        include_e2e_tests=req.include_e2e_tests,
    )

    # Generate with LLM
    max_retries = 2
    for attempt in range(max_retries + 1):
        raw_output = await generate(
            prompt=prompt,
            system=TC_SYSTEM,
            temperature=0.3,
            max_tokens=8192,
        )

        # Split into individual features
        feature_texts = split_features(raw_output)

        if not feature_texts and attempt < max_retries:
            # Retry with correction
            prompt = f"The previous output was not valid Gherkin. Please regenerate.\n\n{prompt}"
            continue

        break

    if not feature_texts:
        raise HTTPException(
            status_code=500,
            detail="Failed to generate valid Gherkin test cases after retries.",
        )

    # Validate and build response
    features = []
    total_scenarios = 0

    for gherkin in feature_texts:
        validation = validate_gherkin(gherkin)
        name = extract_feature_name(gherkin)

        feature = GeneratedFeature(
            name=name,
            gherkin_content=gherkin,
            tags=validation["tags"],
            scenario_count=validation["scenario_count"],
        )
        features.append(feature)
        total_scenarios += validation["scenario_count"]

    return GenerateTestCasesResponse(
        features=features,
        total_scenarios=total_scenarios,
        message=f"Generated {len(features)} feature(s) with {total_scenarios} scenario(s).",
    )


@router.post("/test-code", response_model=GenerateTestCodeResponse)
async def generate_test_code(req: GenerateTestCodeRequest):
    """Generate test code (pytest-bdd or Cucumber.js) from Gherkin."""
    # Optionally retrieve context for implementation details
    context = None
    if req.context_query and req.project_id:
        chunks = await retrieve_context(
            project_id=req.project_id,
            query=req.context_query,
            top_k=5,
        )
        if chunks:
            context = format_context(chunks, max_tokens=2000)

    # Build prompt
    system_prompt, user_prompt = build_code_generation_prompt(
        gherkin_content=req.gherkin_content,
        language=req.language,
        context=context,
    )

    # Generate code
    raw_output = await generate(
        prompt=user_prompt,
        system=system_prompt,
        temperature=0.2,
        max_tokens=8192,
    )

    # Parse output into files
    files = _parse_code_files(raw_output, req.language)

    framework = "pytest-bdd" if req.language == "python" else "cucumber-js"

    return GenerateTestCodeResponse(
        language=req.language,
        framework=framework,
        files=files,
        message=f"Generated {len(files)} file(s) for {framework}.",
    )


def _parse_code_files(raw_output: str, language: str) -> list[GeneratedCodeFile]:
    """Parse LLM output into individual code files."""
    files = []
    pattern = r"===FILE:\s*(.+?)===\s*\n(.*?)===END_FILE==="
    matches = re.findall(pattern, raw_output, re.DOTALL)

    for filename, content in matches:
        filename = filename.strip()
        content = content.strip()

        # Remove any markdown code fences
        content = re.sub(r"^```\w*\s*\n?", "", content)
        content = re.sub(r"\n?```\s*$", "", content)

        # Determine file type
        file_type = "test"
        if "conftest" in filename:
            file_type = "conftest"
        elif "step_def" in filename or "steps" in filename:
            file_type = "step_def"
        elif "world" in filename or "support" in filename:
            file_type = "support"

        files.append(GeneratedCodeFile(
            filename=filename,
            content=content,
            file_type=file_type,
        ))

    # Fallback: if no files parsed, treat entire output as one file
    if not files and raw_output.strip():
        ext = "py" if language == "python" else "js"
        files.append(GeneratedCodeFile(
            filename=f"generated_tests.{ext}",
            content=raw_output.strip(),
            file_type="test",
        ))

    return files
