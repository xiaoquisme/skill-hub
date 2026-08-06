"""Base target adapter interface for multi-platform skill installation."""

from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path
from typing import Optional


class TargetScope(Enum):
    """Installation scope."""
    USER = "user"
    PROJECT = "project"


class TargetAdapter(ABC):
    """Base class for platform-specific skill installation adapters."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Target platform name (e.g., 'hermes', 'claude-code', 'codex')."""

    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description of the target platform."""

    @abstractmethod
    def resolve_path(
        self,
        skill_name: str,
        scope: TargetScope,
        category: Optional[str] = None,
    ) -> Path:
        """Resolve the installation directory for a skill.

        Args:
            skill_name: Name of the skill to install.
            scope: User-level or project-level installation.
            category: Optional category subdirectory (Hermes only).

        Returns:
            Absolute path to the skill's installation directory.
        """

    @abstractmethod
    def write_skill(
        self,
        install_dir: Path,
        files: dict[str, bytes],
    ) -> list[Path]:
        """Write skill files to the target directory.

        Args:
            install_dir: Target directory for the skill.
            files: Dict of filename -> content bytes.

        Returns:
            List of paths that were written.
        """

    def validate_files(self, files: dict[str, bytes]) -> None:
        """Validate files before writing. Override for platform-specific checks."""
        pass
