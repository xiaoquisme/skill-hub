"""Claude Code target adapter."""

from pathlib import Path
from typing import Optional

from skillhub.targets.base import TargetAdapter, TargetScope


class ClaudeCodeAdapter(TargetAdapter):
    """Install skills to Claude Code's skill directory."""

    @property
    def name(self) -> str:
        return "claude-code"

    @property
    def description(self) -> str:
        return "Claude Code"

    def resolve_path(
        self,
        skill_name: str,
        scope: TargetScope,
        category: Optional[str] = None,
    ) -> Path:
        base = Path.home() if scope == TargetScope.USER else Path.cwd()
        return base / ".claude" / "skills" / skill_name

    def write_skill(
        self,
        install_dir: Path,
        files: dict[str, bytes],
    ) -> list[Path]:
        install_dir.mkdir(parents=True, exist_ok=True)
        written = []
        for filename, content in files.items():
            file_path = install_dir / filename
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_bytes(content)
            written.append(file_path)
        return written
