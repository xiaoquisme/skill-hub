"""Authentication endpoints."""

import hashlib
import secrets
from datetime import datetime

from fastapi import APIRouter, Depends

from skillhub.api.deps import get_db, require_auth
from skillhub.database import Database
from skillhub.models import ApiTokenCreate, ApiTokenResponse

router = APIRouter(prefix="/api/auth", tags=["auth"])


def hash_token(token: str) -> str:
    """Hash a token for storage."""
    return hashlib.sha256(token.encode()).hexdigest()


@router.post("/tokens", response_model=ApiTokenResponse)
async def create_token(
    body: ApiTokenCreate,
    _: str = Depends(require_auth),
    db: Database = Depends(get_db),
):
    """Generate a new API token."""
    raw_token = secrets.token_urlsafe(32)
    token_hash = hash_token(raw_token)

    record = await db.create_token(token_hash=token_hash, owner_name=body.owner_name)

    return ApiTokenResponse(
        id=record["id"],
        token=raw_token,
        owner_name=record.get("owner_name"),
        created_at=record["created_at"],
    )
