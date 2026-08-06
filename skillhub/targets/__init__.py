"""Target adapters for multi-platform skill installation."""

from skillhub.targets.base import TargetAdapter, TargetScope
from skillhub.targets.registry import TargetRegistry, registry

__all__ = ["TargetAdapter", "TargetScope", "TargetRegistry", "registry"]
