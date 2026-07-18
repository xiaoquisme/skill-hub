"""Skill CRUD endpoints."""

import json
import os
from pathlib import Path
from typing import Optional

import yaml
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from fastapi.responses import FileResponse

from skillhub.api.deps import get_current_token, get_db, get_storage, require_auth
from skillhub.database import Database
from skillhub.models import SkillCreate, SkillDetail, SkillFileResponse, SkillResponse
from skillhub.storage import SkillStorage

router = APIRouter(prefix="/api/skills", tags=["skills"])


def parse_skill_md(content: bytes) -> dict:
    """Parse SKILL.md frontmatter to extract metadata."""
    text = content.decode("utf-8")
    if not text.startswith("---"):
        return {}

    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}

    try:
        frontmatter = yaml.safe_load(parts[1])
        return frontmatter if isinstance(frontmatter, dict) else {}
    except yaml.YAMLError:
        return {}


@router.get("", response_model=list[SkillResponse])
async def list_skills(
    q: Optional[str] = Query(None, description="Search query"),
    category: Optional[str] = Query(None, description="Filter by category"),
    sort: str = Query("updated_at", description="Sort field"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Database = Depends(get_db),
):
    """List and search skills."""
    skills = await db.list_skills(
        query=q, category=category, sort=sort, limit=limit, offset=offset
    )
    results = []
    for s in skills:
        tags = json.loads(s["tags"]) if s.get("tags") else []
        results.append(
            SkillResponse(
                id=s["id"],
                name=s["name"],
                display_name=s.get("display_name"),
                description=s.get("description"),
                category=s.get("category"),
                tags=tags,
                author=s.get("author"),
                license=s.get("license"),
                created_at=s["created_at"],
                updated_at=s["updated_at"],
                published_by=s.get("published_by"),
            )
        )
    return results


@router.get("/{skill_id}", response_model=SkillDetail)
async def get_skill(skill_id: str, db: Database = Depends(get_db)):
    """Get skill details."""
    skill = await db.get_skill(skill_id)
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")

    files = await db.get_skill_files(skill_id)
    tags = json.loads(skill["tags"]) if skill.get("tags") else []

    return SkillDetail(
        id=skill["id"],
        name=skill["name"],
        display_name=skill.get("display_name"),
        description=skill.get("description"),
        category=skill.get("category"),
        tags=tags,
        author=skill.get("author"),
        license=skill.get("license"),
        created_at=skill["created_at"],
        updated_at=skill["updated_at"],
        published_by=skill.get("published_by"),
        file_count=len(files),
        files=[
            SkillFileResponse(
                filename=f["filename"],
                content_type=f.get("content_type", "text/markdown"),
                size_bytes=f.get("size_bytes"),
            )
            for f in files
        ],
    )


@router.get("/{skill_id}/files/{filename:path}")
async def download_skill_file(
    skill_id: str,
    filename: str,
    db: Database = Depends(get_db),
    storage: SkillStorage = Depends(get_storage),
):
    """Download a skill file."""
    skill = await db.get_skill(skill_id)
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")

    file_path = storage.get_skill_file_path(skill_id, filename)
    if not file_path:
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type="application/octet-stream",
    )


@router.post("", response_model=SkillResponse, status_code=201)
async def publish_skill(
    name: str = Form(...),
    display_name: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    category: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
    author: Optional[str] = Form(None),
    license: Optional[str] = Form(None),
    files: list[UploadFile] = File(default=[]),
    token: str = Depends(require_auth),
    db: Database = Depends(get_db),
    storage: SkillStorage = Depends(get_storage),
):
    """Publish or update a skill."""
    tags_list = json.loads(tags) if tags else []

    # Check if skill with this name already exists
    existing = await db.get_skill_by_name(name)

    if existing:
        # Update existing skill
        skill_id = existing["id"]
        await db.update_skill(
            skill_id,
            display_name=display_name,
            description=description,
            category=category,
            tags=json.dumps(tags_list),
            author=author,
            license=license,
            published_by=token,
        )
    else:
        # Create new skill
        record = await db.create_skill(
            name=name,
            display_name=display_name,
            description=description,
            category=category,
            tags=tags_list,
            author=author,
            license=license,
            published_by=token,
        )
        skill_id = record["id"]

    # Process uploaded files
    for upload_file in files:
        content = await upload_file.read()
        filename = upload_file.filename or "unnamed"
        storage.save_skill_file(skill_id, filename, content)
        await db.add_skill_file(
            skill_id=skill_id,
            filename=filename,
            content_type=upload_file.content_type or "application/octet-stream",
            size_bytes=len(content),
        )

    skill = await db.get_skill(skill_id)
    tags_out = json.loads(skill["tags"]) if skill.get("tags") else []
    return SkillResponse(
        id=skill["id"],
        name=skill["name"],
        display_name=skill.get("display_name"),
        description=skill.get("description"),
        category=skill.get("category"),
        tags=tags_out,
        author=skill.get("author"),
        license=skill.get("license"),
        created_at=skill["created_at"],
        updated_at=skill["updated_at"],
        published_by=skill.get("published_by"),
    )


@router.delete("/{skill_id}", status_code=204)
async def delete_skill(
    skill_id: str,
    token: str = Depends(require_auth),
    db: Database = Depends(get_db),
    storage: SkillStorage = Depends(get_storage),
):
    """Delete a skill."""
    skill = await db.get_skill(skill_id)
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")

    if skill.get("published_by") != token:
        raise HTTPException(status_code=403, detail="Not authorized to delete this skill")

    storage.delete_skill(skill_id)
    await db.delete_skill(skill_id)
    return None
