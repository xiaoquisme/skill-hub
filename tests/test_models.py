"""Tests for data models."""

from datetime import datetime

from skillhub.models import (
    SkillCreate,
    SkillResponse,
    SkillDetail,
    SkillFileResponse,
)


def test_skill_create():
    skill = SkillCreate(name="test-skill")
    assert skill.name == "test-skill"
    assert skill.tags == []
    assert skill.display_name is None


def test_skill_create_with_fields():
    skill = SkillCreate(
        name="my-skill",
        display_name="My Skill",
        description="A test skill",
        category="testing",
        tags=["python", "test"],
        author="tester",
        license="MIT",
    )
    assert skill.name == "my-skill"
    assert skill.tags == ["python", "test"]


def test_skill_response():
    skill = SkillResponse(
        id="test-id",
        name="test-skill",
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    assert skill.id == "test-id"
    assert skill.file_count == 0


def test_skill_detail():
    detail = SkillDetail(
        id="test-id",
        name="test-skill",
        created_at=datetime.now(),
        updated_at=datetime.now(),
        files=[
            SkillFileResponse(filename="SKILL.md", size_bytes=100),
            SkillFileResponse(filename="refs/api.md", size_bytes=50),
        ],
    )
    assert len(detail.files) == 2
    assert detail.files[0].filename == "SKILL.md"
