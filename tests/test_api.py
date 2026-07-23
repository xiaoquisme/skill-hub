"""Tests for API endpoints."""

import tempfile
from pathlib import Path

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

from skillhub.main import app
from skillhub.api import deps
from skillhub.config import AppConfig, StorageConfig
from skillhub.database import Database
from skillhub.storage import SkillStorage


@pytest.mark.asyncio
async def test_health_check():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_list_skills_empty():
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
async def test_database_crud():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = Database(db_path)
        await db.connect()

        skill = await db.create_skill(
            name="test-skill",
            display_name="Test Skill",
            description="A test skill",
            category="testing",
            tags=["python", "test"],
        )
        assert skill["name"] == "test-skill"

        fetched = await db.get_skill(skill["id"])
        assert fetched is not None
        assert fetched["name"] == "test-skill"

        updated = await db.update_skill(skill["id"], description="Updated")
        assert updated["description"] == "Updated"

        deleted = await db.delete_skill(skill["id"])
        assert deleted is True
        assert await db.get_skill(skill["id"]) is None

        await db.close()


@pytest.mark.asyncio
async def test_storage_operations():
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = SkillStorage(Path(tmpdir))

        storage.save_skill_file("skill-1", "SKILL.md", b"# Hello")
        content = storage.get_skill_file("skill-1", "SKILL.md")
        assert content == b"# Hello"

        files = storage.list_skill_files("skill-1")
        assert len(files) == 1

        storage.delete_skill("skill-1")
        assert not storage.skill_exists("skill-1")


@pytest.mark.asyncio
async def test_skill_response_includes_download_count():
    """Test that skill API responses include download_count."""
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

        deps._config = test_config
        deps._db = test_db

        # Create a skill via the database directly
        skill = await test_db.create_skill(
            name="downloadable-skill",
            description="A skill for testing downloads",
            category="testing",
        )

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # List skills and check download_count is present
            response = await client.get("/api/skills")
            assert response.status_code == 200
            skills = response.json()
            assert len(skills) == 1
            assert skills[0]["download_count"] == 0

            # Get skill detail and check download_count
            response = await client.get(f"/api/skills/{skill['id']}")
            assert response.status_code == 200
            detail = response.json()
            assert detail["download_count"] == 0

        await test_db.close()
        deps._db = None
        deps._config = None


@pytest.mark.asyncio
async def test_download_increments_count():
    """Test that downloading a file increments the skill's download_count."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        test_config = AppConfig(
            storage=StorageConfig(
                data_dir=tmpdir_path / "data",
                skills_dir=tmpdir_path / "skills",
            ),
        )
        test_db = Database(test_config.storage.data_dir / "skillhub.db")
        storage = SkillStorage(test_config.storage.skills_dir)
        await test_db.connect()

        deps._config = test_config
        deps._db = test_db
        deps._storage = storage

        # Create a skill with a file
        skill = await test_db.create_skill(name="dl-skill")
        storage.save_skill_file(skill["id"], "SKILL.md", b"# Download me")
        await test_db.add_skill_file(skill["id"], "SKILL.md", "text/markdown", 15)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # Verify initial count
            response = await client.get("/api/skills")
            assert response.json()[0]["download_count"] == 0

            # Download the file
            response = await client.get(
                f"/api/skills/{skill['id']}/files/SKILL.md"
            )
            assert response.status_code == 200

            # Verify count incremented
            response = await client.get("/api/skills")
            assert response.json()[0]["download_count"] == 1

            # Download again
            response = await client.get(
                f"/api/skills/{skill['id']}/files/SKILL.md"
            )
            assert response.status_code == 200

            # Verify count is now 2
            response = await client.get("/api/skills")
            assert response.json()[0]["download_count"] == 2

        await test_db.close()
        deps._db = None
        deps._config = None
        deps._storage = None
