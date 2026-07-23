"""Pydantic models for SkillHub."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class SkillBase(BaseModel):
    name: str
    display_name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    author: Optional[str] = None
    license: Optional[str] = None


class SkillCreate(SkillBase):
    pass


class SkillResponse(SkillBase):
    id: str
    created_at: datetime
    updated_at: datetime
    published_by: Optional[str] = None
    file_count: int = 0
    download_count: int = 0


class SkillDetail(SkillResponse):
    files: list["SkillFileResponse"] = Field(default_factory=list)


class SkillFileResponse(BaseModel):
    filename: str
    content_type: str = "text/markdown"
    size_bytes: Optional[int] = None

SkillDetail.model_rebuild()
