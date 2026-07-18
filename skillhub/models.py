"""Pydantic models for SkillHub."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class SkillBase(BaseModel):
    """Base skill model with common fields."""

    name: str
    display_name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    author: Optional[str] = None
    license: Optional[str] = None


class SkillCreate(SkillBase):
    """Model for creating a skill (includes files)."""

    pass


class SkillResponse(SkillBase):
    """Model for skill responses."""

    id: str
    created_at: datetime
    updated_at: datetime
    published_by: Optional[str] = None
    file_count: int = 0


class SkillDetail(SkillResponse):
    """Detailed skill response with file list."""

    files: list["SkillFileResponse"] = Field(default_factory=list)


class SkillFileResponse(BaseModel):
    """Skill file response."""

    filename: str
    content_type: str = "text/markdown"
    size_bytes: Optional[int] = None


class ApiToken(BaseModel):
    """API token model."""

    id: int
    token_hash: str
    owner_name: Optional[str] = None
    created_at: datetime


class ApiTokenCreate(BaseModel):
    """Model for creating an API token."""

    owner_name: Optional[str] = None


class ApiTokenResponse(BaseModel):
    """API token response (includes the plain token once)."""

    id: int
    token: str
    owner_name: Optional[str] = None
    created_at: datetime


# Rebuild models that reference SkillFileResponse
SkillDetail.model_rebuild()
