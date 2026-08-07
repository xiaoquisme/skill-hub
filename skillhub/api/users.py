"""User management API endpoints (admin only)."""

from fastapi import APIRouter, Depends, HTTPException, Request

from skillhub.api.deps import get_db, require_auth
from skillhub.auth import hash_password
from skillhub.database import Database
from skillhub.models import AdminPasswordReset, UserCreate, UserResponse

router = APIRouter(prefix="/api/users", tags=["users"])


def _user_response(user: dict) -> UserResponse:
    return UserResponse(
        id=user["id"],
        username=user["username"],
        role=user["role"],
        created_at=user["created_at"],
        updated_at=user["updated_at"],
    )


@router.get("", response_model=list[UserResponse])
async def list_users(
    request: Request,
    db: Database = Depends(get_db),
):
    """List all users. Admin only."""
    current_user = await require_auth(request, db)
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    users = await db.list_users()
    return [_user_response(u) for u in users]


@router.post("", response_model=UserResponse, status_code=201)
async def create_user(
    body: UserCreate,
    request: Request,
    db: Database = Depends(get_db),
):
    """Create a new user. Admin only."""
    current_user = await require_auth(request, db)
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    # Check username uniqueness
    existing = await db.get_user_by_username(body.username)
    if existing:
        raise HTTPException(status_code=409, detail="Username already exists")

    # Validate role
    if body.role not in ("admin", "publisher", "viewer"):
        raise HTTPException(status_code=400, detail="Invalid role")

    password_hash = hash_password(body.password)
    user = await db.create_user(
        username=body.username,
        password_hash=password_hash,
        role=body.role,
    )
    return _user_response(user)


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    body: UserCreate,
    request: Request,
    db: Database = Depends(get_db),
):
    """Update a user's role. Admin only."""
    current_user = await require_auth(request, db)
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    target = await db.get_user(user_id)
    if not target:
        raise HTTPException(status_code=404, detail="User not found")

    # Validate role
    if body.role not in ("admin", "publisher", "viewer"):
        raise HTTPException(status_code=400, detail="Invalid role")

    updated = await db.update_user(user_id, role=body.role)
    return _user_response(updated)


@router.delete("/{user_id}", status_code=204)
async def delete_user(
    user_id: str,
    request: Request,
    db: Database = Depends(get_db),
):
    """Delete a user. Admin only. Cannot delete yourself."""
    current_user = await require_auth(request, db)
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    target = await db.get_user(user_id)
    if not target:
        raise HTTPException(status_code=404, detail="User not found")

    # Cannot delete yourself
    if user_id == current_user["id"]:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")

    # Ensure at least one admin remains
    if target["role"] == "admin":
        users = await db.list_users()
        admin_count = sum(1 for u in users if u["role"] == "admin")
        if admin_count <= 1:
            raise HTTPException(
                status_code=400, detail="Cannot delete the last admin user"
            )

    await db.delete_user(user_id)
    return None


@router.post("/{user_id}/reset-password", response_model=UserResponse)
async def reset_password(
    user_id: str,
    body: AdminPasswordReset,
    request: Request,
    db: Database = Depends(get_db),
):
    """Reset a user's password. Admin only."""
    current_user = await require_auth(request, db)
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    target = await db.get_user(user_id)
    if not target:
        raise HTTPException(status_code=404, detail="User not found")

    new_hash = hash_password(body.new_password)
    updated = await db.update_user(user_id, password_hash=new_hash)
    return _user_response(updated)
