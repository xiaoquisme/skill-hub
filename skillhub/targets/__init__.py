"""Target adapters for multi-platform skill installation."""

from skillhub.targets.base import TargetAdapter, TargetScope
from skillhub.targets.registry import TargetRegistry, registry
from skillhub.targets.hermes import HermesAdapter
from skillhub.targets.claude_code import ClaudeCodeAdapter
from skillhub.targets.codex import CodexAdapter

# Register built-in adapters
registry.register(HermesAdapter())
registry.register(ClaudeCodeAdapter())
registry.register(CodexAdapter())

__all__ = [
    "TargetAdapter", "TargetScope", "TargetRegistry", "registry",
    "HermesAdapter", "ClaudeCodeAdapter", "CodexAdapter",
]
