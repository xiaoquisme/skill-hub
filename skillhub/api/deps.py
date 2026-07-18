"""Dependency injection for FastAPI."""

from pathlib import Path
from typing import Optional

from fastapi import Depends, Header, HTTPException

from skillhub.config import AppConfig, load_config
from skillhub.database import Database
from skillhub.storage import SkillStorage

_config: Optional[AppConfig] = None
_db: Optional[Database] = None
_storage: Optional[SkillStorage] = None


async def get_config() -> AppConfig:
    """Get application configuration."""
    global _config
    if _config is None:
        _config = load_config()
    return _config


async def get_db(config: AppConfig = Depends(get_config)) -> Database:
    """Get database instance."""
    global _db
    if _db is None:
        _db = Database(config.storage.data_dir / "skillhub.db")
        await _db.connect()
    return _db


async def get_storage(config: AppConfig = Depends(get_config)) -> SkillStorage:
    """Get storage instance."""
    global _storage
    if _storage is None:
        _storage = SkillStorage(config.storage.skills_dir)
    return _storage


async def get_current_token(
    authorization: Optional[str] = Header(None),
    db: Database = Depends(get_db),
) -> Optional[str]:
    """Extract and validate API token from Authorization header.

    Returns the token hash if valid, None if no token provided.
    Raises HTTPException if token is invalid.
    """
    if not authorization:
        return None

    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    token = authorization[7:]  # Strip "Bearer " prefix
    token_record = await db.validate_token(token)
    if not token_record:
        raise HTTPException(status_code=401, detail="Invalid API token")

    return token


async def require_auth(
    token: Optional[str] = Depends(get_current_token),
) -> str:
    """Require authentication. Raises 401 if no valid token."""
    if not token:
        raise HTTPException(status_code=401, detail="Authentication required")
    return token
