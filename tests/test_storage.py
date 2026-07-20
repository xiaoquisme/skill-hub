"""Tests for storage operations."""

import tempfile
from pathlib import Path

import pytest

from skillhub.storage import SkillStorage


@pytest.fixture
def storage():
    """Create a temporary storage directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield SkillStorage(Path(tmpdir))


def test_save_and_get_file(storage):
    """Test saving and retrieving a file."""
    storage.save_skill_file("skill-1", "SKILL.md", b"# Hello")
    content = storage.get_skill_file("skill-1", "SKILL.md")
    assert content == b"# Hello"


def test_save_multiple_files(storage):
    """Test saving multiple files."""
    files = {
        "SKILL.md": b"# Skill",
        "refs/api.md": b"# API",
        "scripts/run.py": b"print('hello')",
    }
    storage.save_skill_files("skill-1", files)

    assert storage.get_skill_file("skill-1", "SKILL.md") == b"# Skill"
    assert storage.get_skill_file("skill-1", "refs/api.md") == b"# API"
    assert storage.get_skill_file("skill-1", "scripts/run.py") == b"print('hello')"


def test_list_files(storage):
    """Test listing files."""
    storage.save_skill_file("skill-1", "SKILL.md", b"content")
    storage.save_skill_file("skill-1", "README.md", b"content")

    files = storage.list_skill_files("skill-1")
    assert len(files) == 2
    assert "README.md" in files
    assert "SKILL.md" in files


def test_delete_skill(storage):
    """Test deleting a skill."""
    storage.save_skill_file("skill-1", "SKILL.md", b"content")
    assert storage.skill_exists("skill-1")

    storage.delete_skill("skill-1")
    assert not storage.skill_exists("skill-1")


def test_get_nonexistent_file(storage):
    """Test getting a file that doesn't exist."""
    content = storage.get_skill_file("skill-1", "missing.md")
    assert content is None


def test_skill_size(storage):
    """Test getting skill size."""
    storage.save_skill_file("skill-1", "SKILL.md", b"hello world")
    storage.save_skill_file("skill-1", "README.md", b"readme")

    size = storage.get_skill_size("skill-1")
    assert size == len(b"hello world") + len(b"readme")
