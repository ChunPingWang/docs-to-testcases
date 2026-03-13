"""Provider management API — register, switch, update, and remove model providers."""

from fastapi import APIRouter, HTTPException

from app.core.llm.provider_registry import ProviderConfig, ProviderRegistry, provider_registry
from app.models.requests import RegisterProviderRequest, UpdateProviderRequest, SwitchProviderRequest
from app.models.responses import ProviderResponse, ProviderListResponse

router = APIRouter()


def _provider_to_response(p: ProviderConfig) -> ProviderResponse:
    return ProviderResponse(
        name=p.name,
        base_url=p.base_url,
        api_key_set=bool(p.api_key),
        llm_model=p.llm_model,
        embedding_model=p.embedding_model,
        supports_streaming=p.supports_streaming,
        supports_finetune=p.supports_finetune,
        supports_embedding=p.supports_embedding,
        optimization_mode=p.optimization_mode,
    )


@router.get("", response_model=ProviderListResponse)
async def list_providers():
    """List all registered providers and which one is active."""
    return ProviderListResponse(
        active_provider=provider_registry.active_name,
        providers=[_provider_to_response(p) for p in provider_registry.list_all()],
    )


@router.post("", response_model=ProviderResponse, status_code=201)
async def register_provider(req: RegisterProviderRequest):
    """Register a new model provider at runtime."""
    if req.optimization_mode not in ProviderRegistry.VALID_OPTIMIZATION_MODES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid optimization_mode. Must be one of: {ProviderRegistry.VALID_OPTIMIZATION_MODES}",
        )
    if provider_registry.get(req.name):
        raise HTTPException(status_code=409, detail=f"Provider '{req.name}' already exists.")

    config = ProviderConfig(
        name=req.name,
        base_url=req.base_url,
        api_key=req.api_key,
        llm_model=req.llm_model,
        embedding_model=req.embedding_model,
        supports_streaming=req.supports_streaming,
        supports_finetune=req.supports_finetune,
        supports_embedding=req.supports_embedding,
        optimization_mode=req.optimization_mode,
    )
    provider_registry.register(config)
    return _provider_to_response(config)


@router.get("/{name}", response_model=ProviderResponse)
async def get_provider(name: str):
    """Get details of a specific provider."""
    p = provider_registry.get(name)
    if not p:
        raise HTTPException(status_code=404, detail=f"Provider '{name}' not found.")
    return _provider_to_response(p)


@router.put("/{name}", response_model=ProviderResponse)
async def update_provider(name: str, req: UpdateProviderRequest):
    """Partially update an existing provider's configuration."""
    data = req.model_dump(exclude_none=True)
    if "optimization_mode" in data and data["optimization_mode"] not in ProviderRegistry.VALID_OPTIMIZATION_MODES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid optimization_mode. Must be one of: {ProviderRegistry.VALID_OPTIMIZATION_MODES}",
        )
    p = provider_registry.update(name, data)
    if not p:
        raise HTTPException(status_code=404, detail=f"Provider '{name}' not found.")
    return _provider_to_response(p)


@router.delete("/{name}")
async def delete_provider(name: str):
    """Remove a provider from the registry."""
    if not provider_registry.unregister(name):
        raise HTTPException(status_code=404, detail=f"Provider '{name}' not found.")
    return {"status": "deleted", "name": name}


@router.post("/switch", response_model=ProviderResponse)
async def switch_provider(req: SwitchProviderRequest):
    """Switch the active provider. All subsequent LLM/embedding calls will use it."""
    if not provider_registry.set_active(req.name):
        raise HTTPException(status_code=404, detail=f"Provider '{req.name}' not found.")
    p = provider_registry.get_active()
    return _provider_to_response(p)
