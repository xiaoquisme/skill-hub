"""Password hashing and JWT token utilities for SkillHub."""

import os
import secrets
import warnings

import bcrypt
import jwt

# JWT secret key - from environment or auto-generated
def _get_secret_key() -> str:
    key = os.environ.get("SKILLHUB_SECRET_KEY")
    if key:
        return key
    # Generate a random key and warn
    key = secrets.token_hex(32)
    warnings.warn(
        "SKILLHUB_SECRET_KEY not set. Using auto-generated key. "
        "Tokens will not persist across restarts. "
        "Set SKILLHUB_SECRET_KEY environment variable for production.",
        stacklevel=2,
    )
    return key

SECRET_KEY = _get_secret_key()
ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    password_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password_bytes, salt).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against a bcrypt hash."""
    password_bytes = password.encode("utf-8")
    hashed_bytes = hashed.encode("utf-8")
    return bcrypt.checkpw(password_bytes, hashed_bytes)


def create_token(user_id: str, role: str) -> str:
    """Create a JWT token for a user. No expiration."""
    payload = {
        "user_id": user_id,
        "role": role,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    """Decode and verify a JWT token. Returns the payload dict.
    
    Raises jwt.InvalidTokenError if the token is invalid.
    """
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
