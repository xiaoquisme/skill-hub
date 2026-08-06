"""Codex target adapter."""

from pathlib import Path
from typing import Optional

from skillhub.targets.base import TargetAdapter, TargetScope


class CodexAdapter(TargetAdapter):
    """Install skills to Codex's agent directory."""

    @property
    def name(self) -> str:
        return "codex"

    @property
    def description(self) -> str:
        return "Codex"

    def resolve_path(
        self,
        skill_name: str,
        scope: TargetScope,
        category: Optional[str] = None,
    ) -> Path:
        base = Path.home() if scope == TargetScope.USER else Path.cwd()
        return base / ".codex" / "agents" / skill_name

    def write_skill(
        self,
        install_dir: Path,
        files: dict[str, bytes],
    ) -> list[Path]:
        install_dir.mkdir(parents=True, exist_ok=True)
        written = []
        for filename, content in files.items():
            # Rename SKILL.md to AGENTS.md for Codex compatibility
            if filename == "SKILL.md":
                filename = "AGENTS.md"
            file_path = install_dir / filename
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_bytes(content)
            written.append(file_path)
        return written
