"""Tests for API endpoints (simplified)."""

import tempfile
from pathlib import Path

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

from skillhub.main import app
from skillhub.api import deps
from skillhub.config import AppConfig, StorageConfig, ServerConfig
from skillhub.database import Database
from skillhub.storage import SkillStorage


@pytest.mark.asyncio
async def test_health_check():
    """Test health endpoint."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_list_skills_empty():
    """Test listing skills when empty."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        test_config = AppConfig(
            storage=StorageConfig(
                data_dir=tmpdir_path / "data",
                skills_dir=tmpdir_path / "skills",
            ),
        )
        test_db = Database(test_config.storage.data_dir / "skillhub.db")
        await test_db.connect()

        # Override the global db
        deps._config = test_config
        deps._db = test_db

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/skills")
            assert response.status_code == 200
            assert response.json() == []

        await test_db.close()
        deps._db = None
        deps._config = None


@pytest.mark.asyncio
async def test_auth_required():
    """Test that auth is required for publishing."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/skills",
            data={"name": "no-auth"},
        )
        assert response.status_code == 401


@pytest.mark.asyncio
async def test_database_crud():
    """Test database CRUD operations directly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = Database(db_path)
        await db.connect()

        # Create
        skill = await db.create_skill(
            name="test-skill",
            display_name="Test Skill",
            description="A test skill",
            category="testing",
            tags=["python", "test"],
        )
        assert skill["name"] == "test-skill"

        # Read
        fetched = await db.get_skill(skill["id"])
        assert fetched is not None
        assert fetched["name"] == "test-skill"

        # Update
        updated = await db.update_skill(skill["id"], description="Updated")
        assert updated["description"] == "Updated"

        # Delete
        deleted = await db.delete_skill(skill["id"])
        assert deleted is True
        assert await db.get_skill(skill["id"]) is None

        await db.close()


@pytest.mark.asyncio
async def test_storage_operations():
    """Test storage operations directly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = SkillStorage(Path(tmpdir))

        # Save file
        storage.save_skill_file("skill-1", "SKILL.md", b"# Hello")
        content = storage.get_skill_file("skill-1", "SKILL.md")
        assert content == b"# Hello"

        # List files
        files = storage.list_skill_files("skill-1")
        assert len(files) == 1

        # Delete
        storage.delete_skill("skill-1")
        assert not storage.skill_exists("skill-1")
