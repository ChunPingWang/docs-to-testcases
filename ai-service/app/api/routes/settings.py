from fastapi import APIRouter

from app.models.requests import UpdateSettingsRequest
from app.models.responses import SettingsResponse
from app.core.runtime_settings import runtime_settings

router = APIRouter()


@router.get("", response_model=SettingsResponse)
async def get_settings():
    """Return current runtime settings."""
    return SettingsResponse(**runtime_settings.to_dict())


@router.put("", response_model=SettingsResponse)
async def update_settings(req: UpdateSettingsRequest):
    """Partially update runtime settings."""
    updated = runtime_settings.update(req.model_dump(exclude_none=True))
    return SettingsResponse(**updated)


@router.post("/reset", response_model=SettingsResponse)
async def reset_settings():
    """Reset all settings to defaults."""
    runtime_settings.reset()
    return SettingsResponse(**runtime_settings.to_dict())
