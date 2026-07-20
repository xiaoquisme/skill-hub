"""Skill CRUD endpoints."""

import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from fastapi.responses import FileResponse

from skillhub.api.deps import get_current_token, get_db, get_storage, require_auth
from skillhub.database import Database
from skillhub.models import SkillDetail, SkillFileResponse, SkillResponse
from skillhub.parsing import parse_frontmatter
from skillhub.storage import SkillStorage

router = APIRouter(prefix="/api/skills", tags=["skills"])


def _skill_from_row(row: dict) -> SkillResponse:
    tags = json.loads(row["tags"]) if row.get("tags") else []
    return SkillResponse(
        id=row["id"],
        name=row["name"],
        display_name=row.get("display_name"),
        description=row.get("description"),
        category=row.get("category"),
        tags=tags,
        author=row.get("author"),
        license=row.get("license"),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        published_by=row.get("published_by"),
    )


@router.get("", response_model=list[SkillResponse])
async def list_skills(
    q: Optional[str] = Query(None, description="Search query"),
    category: Optional[str] = Query(None, description="Filter by category"),
    sort: str = Query("updated_at", description="Sort field"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Database = Depends(get_db),
):
    skills = await db.list_skills(
        query=q, category=category, sort=sort, limit=limit, offset=offset
    )
    return [_skill_from_row(s) for s in skills]


@router.get("/{skill_id}", response_model=SkillDetail)
async def get_skill(skill_id: str, db: Database = Depends(get_db)):
    skill = await db.get_skill(skill_id)
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")

    files = await db.get_skill_files(skill_id)

    return SkillDetail(
        **_skill_from_row(skill).model_dump(),
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
    tags_list = json.loads(tags) if tags else []

    existing = await db.get_skill_by_name(name)

    if existing:
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

    updated = await db.get_skill(skill_id)
    assert updated is not None
    return _skill_from_row(updated)


@router.delete("/{skill_id}", status_code=204)
async def delete_skill(
    skill_id: str,
    token: str = Depends(require_auth),
    db: Database = Depends(get_db),
    storage: SkillStorage = Depends(get_storage),
):
    skill = await db.get_skill(skill_id)
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")

    if skill.get("published_by") != token:
        raise HTTPException(status_code=403, detail="Not authorized to delete this skill")

    storage.delete_skill(skill_id)
    await db.delete_skill(skill_id)
    return None
