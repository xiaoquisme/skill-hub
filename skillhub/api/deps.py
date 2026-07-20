"""Dependency injection for FastAPI."""

from typing import Optional

from fastapi import Depends

from skillhub.config import AppConfig, load_config
from skillhub.database import Database
from skillhub.storage import SkillStorage

_config: Optional[AppConfig] = None
_db: Optional[Database] = None
_storage: Optional[SkillStorage] = None


async def get_config() -> AppConfig:
    global _config
    if _config is None:
        _config = load_config()
    return _config


async def get_db(config: AppConfig = Depends(get_config)) -> Database:
    global _db
    if _db is None:
        _db = Database(config.storage.data_dir / "skillhub.db")
        await _db.connect()
    return _db


async def get_storage(config: AppConfig = Depends(get_config)) -> SkillStorage:
    global _storage
    if _storage is None:
        _storage = SkillStorage(config.storage.skills_dir)
    return _storage
