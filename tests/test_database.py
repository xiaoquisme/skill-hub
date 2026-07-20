"""Tests for database operations."""

import tempfile
from pathlib import Path

import pytest
import pytest_asyncio

from skillhub.database import Database


@pytest_asyncio.fixture
async def db():
    """Create a temporary database for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        database = Database(db_path)
        await database.connect()
        yield database
        await database.close()


@pytest.mark.asyncio
async def test_create_skill(db):
    """Test creating a skill."""
    skill = await db.create_skill(
        name="test-skill",
        display_name="Test Skill",
        description="A test skill",
        category="testing",
        tags=["python", "test"],
        author="tester",
    )
    assert skill["name"] == "test-skill"
    assert skill["display_name"] == "Test Skill"
    assert "id" in skill


@pytest.mark.asyncio
async def test_get_skill(db):
    """Test getting a skill by ID."""
    created = await db.create_skill(name="get-me")
    fetched = await db.get_skill(created["id"])
    assert fetched is not None
    assert fetched["name"] == "get-me"


@pytest.mark.asyncio
async def test_get_skill_by_name(db):
    """Test getting a skill by name."""
    await db.create_skill(name="named-skill")
    found = await db.get_skill_by_name("named-skill")
    assert found is not None
    assert found["name"] == "named-skill"


@pytest.mark.asyncio
async def test_update_skill(db):
    """Test updating a skill."""
    created = await db.create_skill(name="update-me")
    updated = await db.update_skill(created["id"], description="Updated description")
    assert updated["description"] == "Updated description"


@pytest.mark.asyncio
async def test_delete_skill(db):
    """Test deleting a skill."""
    created = await db.create_skill(name="delete-me")
    result = await db.delete_skill(created["id"])
    assert result is True
    assert await db.get_skill(created["id"]) is None


@pytest.mark.asyncio
async def test_list_skills(db):
    """Test listing skills."""
    await db.create_skill(name="skill-1")
    await db.create_skill(name="skill-2")
    await db.create_skill(name="skill-3")

    skills = await db.list_skills()
    assert len(skills) == 3


@pytest.mark.asyncio
async def test_list_skills_with_query(db):
    """Test listing skills with search query."""
    await db.create_skill(name="python-tool", description="A Python tool")
    await db.create_skill(name="js-tool", description="A JavaScript tool")

    skills = await db.list_skills(query="python")
    assert len(skills) == 1
    assert skills[0]["name"] == "python-tool"


@pytest.mark.asyncio
async def test_list_skills_with_category(db):
    """Test listing skills with category filter."""
    await db.create_skill(name="skill-a", category="testing")
    await db.create_skill(name="skill-b", category="production")

    skills = await db.list_skills(category="testing")
    assert len(skills) == 1
    assert skills[0]["name"] == "skill-a"


@pytest.mark.asyncio
async def test_count_skills(db):
    """Test counting skills."""
    await db.create_skill(name="count-1")
    await db.create_skill(name="count-2")

    count = await db.count_skills()
    assert count == 2


@pytest.mark.asyncio
async def test_skill_files(db):
    """Test skill file operations."""
    skill = await db.create_skill(name="file-skill")

    await db.add_skill_file(skill["id"], "SKILL.md", "text/markdown", 100)
    await db.add_skill_file(skill["id"], "refs/api.md", "text/markdown", 50)

    files = await db.get_skill_files(skill["id"])
    assert len(files) == 2

    await db.delete_skill_files(skill["id"])
    files = await db.get_skill_files(skill["id"])
    assert len(files) == 0
