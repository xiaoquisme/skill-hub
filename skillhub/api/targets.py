"""Target discovery endpoint."""

from fastapi import APIRouter, Depends

from skillhub.api.deps import get_config
from skillhub.config import AppConfig
from skillhub.targets import registry

router = APIRouter(prefix="/api/targets", tags=["targets"])


@router.get("")
async def list_targets(config: AppConfig = Depends(get_config)):
    """List available installation targets with their configured defaults."""
    targets = []
    for adapter in registry.list_all():
        target_config = config.targets.get(adapter.name)
        enabled = target_config.enabled if target_config else True
        targets.append({
            "name": adapter.name,
            "description": adapter.description,
            "scope": target_config.scope if target_config else "user",
            "enabled": enabled,
        })
    default_target = next(iter(config.targets.keys()), "hermes")
    return {
        "targets": targets,
        "default": default_target,
    }
