"""Tests for data models."""

import pytest
from skillhub.models import (
    SkillCreate,
    SkillResponse,
    SkillDetail,
    SkillFileResponse,
    ApiTokenCreate,
    ApiTokenResponse,
)


def test_skill_create():
    """Test SkillCreate model."""
    skill = SkillCreate(name="test-skill")
    assert skill.name == "test-skill"
    assert skill.tags == []
    assert skill.display_name is None


def test_skill_create_with_fields():
    """Test SkillCreate with all fields."""
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
    """Test SkillResponse model."""
    from datetime import datetime

    skill = SkillResponse(
        id="test-id",
        name="test-skill",
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    assert skill.id == "test-id"
    assert skill.file_count == 0


def test_skill_detail():
    """Test SkillDetail model with files."""
    from datetime import datetime

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


def test_api_token_create():
    """Test ApiTokenCreate model."""
    token = ApiTokenCreate(owner_name="testuser")
    assert token.owner_name == "testuser"


def test_api_token_create_no_owner():
    """Test ApiTokenCreate without owner."""
    token = ApiTokenCreate()
    assert token.owner_name is None
