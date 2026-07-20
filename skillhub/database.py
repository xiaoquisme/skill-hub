"""SQLite database operations for SkillHub."""

import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Optional

import aiosqlite


SCHEMA = """
CREATE TABLE IF NOT EXISTS skills (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    display_name TEXT,
    description TEXT,
    category TEXT,
    tags TEXT,
    author TEXT,
    license TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    published_by TEXT
);

CREATE TABLE IF NOT EXISTS skill_files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    skill_id TEXT NOT NULL REFERENCES skills(id) ON DELETE CASCADE,
    filename TEXT NOT NULL,
    content_type TEXT DEFAULT 'text/markdown',
    size_bytes INTEGER,
    UNIQUE(skill_id, filename)
);
"""

ALLOWED_SORT_FIELDS = {"created_at", "updated_at", "name", "category"}


class Database:

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._conn: Optional[aiosqlite.Connection] = None

    async def connect(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = await aiosqlite.connect(str(self.db_path))
        self._conn.row_factory = aiosqlite.Row
        await self._conn.executescript(SCHEMA)
        await self._conn.execute("PRAGMA foreign_keys = ON")
        await self._conn.commit()

    async def close(self) -> None:
        if self._conn:
            await self._conn.close()
            self._conn = None

    @property
    def conn(self) -> aiosqlite.Connection:
        if not self._conn:
            raise RuntimeError("Database not connected. Call connect() first.")
        return self._conn

    def _build_filter(
        self, query: Optional[str], category: Optional[str]
    ) -> tuple[list[str], list]:
        conditions, params = [], []
        if query:
            conditions.append(
                "(name LIKE ? OR display_name LIKE ? OR description LIKE ?)"
            )
            q = f"%{query}%"
            params.extend([q, q, q])
        if category:
            conditions.append("category = ?")
            params.append(category)
        return conditions, params

    # --- Skills CRUD ---

    async def create_skill(
        self,
        name: str,
        display_name: Optional[str] = None,
        description: Optional[str] = None,
        category: Optional[str] = None,
        tags: Optional[list[str]] = None,
        author: Optional[str] = None,
        license: Optional[str] = None,
        published_by: Optional[str] = None,
    ) -> dict:
        skill_id = str(uuid.uuid4())
        now = datetime.now(UTC).isoformat()
        tags_json = json.dumps(tags or [])

        await self.conn.execute(
            """INSERT INTO skills (id, name, display_name, description, category,
               tags, author, license, created_at, updated_at, published_by)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (skill_id, name, display_name, description, category,
             tags_json, author, license, now, now, published_by),
        )
        await self.conn.commit()
        return await self.get_skill(skill_id)

    async def get_skill(self, skill_id: str) -> Optional[dict]:
        async with self.conn.execute(
            "SELECT * FROM skills WHERE id = ?", (skill_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return dict(row)
        return None

    async def get_skill_by_name(self, name: str) -> Optional[dict]:
        async with self.conn.execute(
            "SELECT * FROM skills WHERE name = ?", (name,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return dict(row)
        return None

    async def update_skill(self, skill_id: str, **kwargs) -> Optional[dict]:
        kwargs["updated_at"] = datetime.now(UTC).isoformat()
        set_clause = ", ".join(f"{k} = ?" for k in kwargs)
        values = list(kwargs.values()) + [skill_id]

        await self.conn.execute(
            f"UPDATE skills SET {set_clause} WHERE id = ?", values
        )
        await self.conn.commit()
        return await self.get_skill(skill_id)

    async def delete_skill(self, skill_id: str) -> bool:
        async with self.conn.execute(
            "DELETE FROM skills WHERE id = ?", (skill_id,)
        ) as cursor:
            await self.conn.commit()
            return cursor.rowcount > 0

    async def list_skills(
        self,
        query: Optional[str] = None,
        category: Optional[str] = None,
        sort: str = "updated_at",
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict]:
        conditions, params = self._build_filter(query, category)
        where = " WHERE " + " AND ".join(conditions) if conditions else ""
        sort_col = sort if sort in ALLOWED_SORT_FIELDS else "updated_at"
        order = f" ORDER BY {sort_col} DESC"
        params.extend([limit, offset])

        async with self.conn.execute(
            f"SELECT * FROM skills{where}{order} LIMIT ? OFFSET ?", params
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def count_skills(
        self, query: Optional[str] = None, category: Optional[str] = None
    ) -> int:
        conditions, params = self._build_filter(query, category)
        where = " WHERE " + " AND ".join(conditions) if conditions else ""

        async with self.conn.execute(
            f"SELECT COUNT(*) FROM skills{where}", params
        ) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0

    # --- Skill Files ---

    async def add_skill_file(
        self,
        skill_id: str,
        filename: str,
        content_type: str = "text/markdown",
        size_bytes: Optional[int] = None,
    ) -> None:
        await self.conn.execute(
            """INSERT OR REPLACE INTO skill_files (skill_id, filename, content_type, size_bytes)
               VALUES (?, ?, ?, ?)""",
            (skill_id, filename, content_type, size_bytes),
        )
        await self.conn.commit()

    async def get_skill_files(self, skill_id: str) -> list[dict]:
        async with self.conn.execute(
            "SELECT * FROM skill_files WHERE skill_id = ? ORDER BY filename",
            (skill_id,),
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def delete_skill_files(self, skill_id: str) -> None:
        await self.conn.execute(
            "DELETE FROM skill_files WHERE skill_id = ?", (skill_id,)
        )
        await self.conn.commit()
