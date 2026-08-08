"""Auth API endpoints - login and password management."""

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse

from skillhub.api.deps import get_db, require_auth
from skillhub.auth import hash_password, verify_password
from skillhub.database import Database
from skillhub.models import (
    LoginRequest,
    TokenResponse,
    UserPasswordChange,
    UserResponse,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: Database = Depends(get_db)):
    """Authenticate user and return JWT token."""
    user = await db.get_user_by_username(request.username)
    if not user or not verify_password(request.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    from skillhub.auth import create_token
    token = create_token(user["id"], user["role"])

    # Set token as HttpOnly cookie for UI auth middleware
    response = JSONResponse(content=TokenResponse(access_token=token).model_dump())
    response.set_cookie(
        key="skillhub_token",
        value=token,
        httponly=True,
        samesite="lax",
        max_age=86400 * 30,  # 30 days
    )
    return response


@router.post("/logout")
async def logout():
    """Clear the auth cookie."""
    response = JSONResponse(content={"detail": "Logged out"})
    response.delete_cookie(key="skillhub_token")
    return response


@router.post("/change-password", response_model=UserResponse)
async def change_password(
    body: UserPasswordChange,
    request: Request,
    db: Database = Depends(get_db),
):
    """Change the current user's own password."""
    current_user = await require_auth(request, db)

    if not verify_password(body.old_password, current_user["password_hash"]):
        raise HTTPException(status_code=400, detail="Current password is incorrect")

    new_hash = hash_password(body.new_password)
    updated = await db.update_user(current_user["id"], password_hash=new_hash)
    return UserResponse(
        id=updated["id"],
        username=updated["username"],
        role=updated["role"],
        created_at=updated["created_at"],
        updated_at=updated["updated_at"],
    )
