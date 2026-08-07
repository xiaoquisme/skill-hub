"""Dependency injection for FastAPI."""

from typing import Optional

from fastapi import Depends, HTTPException, Request

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


async def get_current_user(request: Request, db: Database = Depends(get_db)) -> Optional[dict]:
    """Extract user from JWT token in Authorization header.
    
    Returns user dict if valid, None if no token or invalid token.
    Used for endpoints that optionally need auth.
    """
    from skillhub.auth import decode_token

    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None

    token = auth_header[7:]  # Remove "Bearer " prefix
    try:
        payload = decode_token(token)
    except Exception:
        return None

    user_id = payload.get("user_id")
    if not user_id:
        return None

    user = await db.get_user(user_id)
    return user


async def require_auth(request: Request, db: Optional[Database] = None) -> dict:
    """Require a valid JWT token. Raises 401 if not authenticated.
    
    Returns the user dict. Used for write endpoints that require auth.
    """
    from skillhub.auth import decode_token

    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authentication required")

    token = auth_header[7:]
    try:
        payload = decode_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    if db is None:
        db = await get_db()

    user = await db.get_user(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user
