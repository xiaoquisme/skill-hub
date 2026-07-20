"""File storage operations for SkillHub."""

import shutil
from pathlib import Path
from typing import Optional


class SkillStorage:
    """Manages skill file storage on the local filesystem."""

    def __init__(self, skills_dir: Path):
        self.skills_dir = skills_dir
        self.skills_dir.mkdir(parents=True, exist_ok=True)

    def _skill_path(self, skill_id: str) -> Path:
        """Get the path for a skill's files."""
        return self.skills_dir / skill_id

    def save_skill_files(self, skill_id: str, files: dict[str, bytes]) -> None:
        """Save skill files to disk.

        Args:
            skill_id: The skill's unique ID.
            files: Dict of filename -> content bytes.
        """
        skill_dir = self._skill_path(skill_id)
        skill_dir.mkdir(parents=True, exist_ok=True)

        for filename, content in files.items():
            file_path = skill_dir / filename
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_bytes(content)

    def save_skill_file(self, skill_id: str, filename: str, content: bytes) -> None:
        """Save a single skill file to disk."""
        skill_dir = self._skill_path(skill_id)
        file_path = skill_dir / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_bytes(content)

    def get_skill_file(self, skill_id: str, filename: str) -> Optional[bytes]:
        """Retrieve a skill file's content."""
        file_path = self._skill_path(skill_id) / filename
        if file_path.exists():
            return file_path.read_bytes()
        return None

    def get_skill_file_path(self, skill_id: str, filename: str) -> Optional[Path]:
        """Get the path to a skill file."""
        file_path = self._skill_path(skill_id) / filename
        if file_path.exists():
            return file_path
        return None

    def list_skill_files(self, skill_id: str) -> list[str]:
        """List all files in a skill directory."""
        skill_dir = self._skill_path(skill_id)
        if not skill_dir.exists():
            return []

        files = []
        for path in skill_dir.rglob("*"):
            if path.is_file():
                rel = path.relative_to(skill_dir)
                files.append(str(rel))
        return sorted(files)

    def delete_skill(self, skill_id: str) -> bool:
        """Delete all files for a skill."""
        skill_dir = self._skill_path(skill_id)
        if skill_dir.exists():
            shutil.rmtree(skill_dir)
            return True
        return False

    def skill_exists(self, skill_id: str) -> bool:
        """Check if a skill directory exists."""
        return self._skill_path(skill_id).is_dir()

    def get_skill_size(self, skill_id: str) -> int:
        """Get total size of a skill's files in bytes."""
        skill_dir = self._skill_path(skill_id)
        if not skill_dir.exists():
            return 0
        return sum(f.stat().st_size for f in skill_dir.rglob("*") if f.is_file())
