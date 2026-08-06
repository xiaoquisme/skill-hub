"""Target discovery endpoint."""

from fastapi import APIRouter, Depends

from skillhub.config import AppConfig, load_config
from skillhub.targets import registry

router = APIRouter(prefix="/api/targets", tags=["targets"])


@router.get("")
async def list_targets():
    """List available installation targets with their configured defaults."""
    config = load_config()
    targets = []
    for adapter in registry.list_all():
        target_config = config.targets.get(adapter.name)
        targets.append({
            "name": adapter.name,
            "description": adapter.description,
            "scope": target_config.scope if target_config else "user",
            "enabled": target_config.enabled if target_config else True,
        })
    default_target = next(iter(config.targets.keys()), "hermes")
    return {
        "targets": targets,
        "default": default_target,
    }
