"""Target adapter registry."""

from typing import Optional

from skillhub.targets.base import TargetAdapter, TargetScope


class TargetRegistry:
    """Registry of platform-specific target adapters."""

    def __init__(self):
        self._adapters: dict[str, TargetAdapter] = {}

    def register(self, adapter: TargetAdapter) -> None:
        """Register a target adapter."""
        self._adapters[adapter.name] = adapter

    def get(self, name: str) -> Optional[TargetAdapter]:
        """Get adapter by name, or None if not found."""
        return self._adapters.get(name)

    def get_or_raise(self, name: str) -> TargetAdapter:
        """Get adapter by name, raising KeyError if not found."""
        adapter = self._adapters.get(name)
        if adapter is None:
            available = ", ".join(sorted(self._adapters.keys()))
            raise KeyError(
                f"Unknown target '{name}'. Available targets: {available}"
            )
        return adapter

    @property
    def targets(self) -> list[str]:
        """List registered target names."""
        return sorted(self._adapters.keys())

    def list_all(self) -> list[TargetAdapter]:
        """List all registered adapters."""
        return [self._adapters[name] for name in sorted(self._adapters.keys())]


# Global registry instance
registry = TargetRegistry()
