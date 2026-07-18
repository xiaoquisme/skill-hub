"""SQLite database operations for SkillHub."""

import uuid
from datetime import datetime
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

CREATE TABLE IF NOT EXISTS api_tokens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    token_hash TEXT NOT NULL UNIQUE,
    owner_name TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""


class Database:
    """Async SQLite database manager."""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._conn: Optional[aiosqlite.Connection] = None

    async def connect(self) -> None:
        """Connect to the database and initialize schema."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = await aiosqlite.connect(str(self.db_path))
        self._conn.row_factory = aiosqlite.Row
        await self._conn.executescript(SCHEMA)
        await self._conn.execute("PRAGMA foreign_keys = ON")
        await self._conn.commit()

    async def close(self) -> None:
        """Close the database connection."""
        if self._conn:
            await self._conn.close()
            self._conn = None

    @property
    def conn(self) -> aiosqlite.Connection:
        """Get the active connection."""
        if not self._conn:
            raise RuntimeError("Database not connected. Call connect() first.")
        return self._conn

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
        """Create a new skill record. Returns the created skill."""
        skill_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        tags_json = "[]" if not tags else str(tags)

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
        """Get a skill by ID."""
        async with self.conn.execute(
            "SELECT * FROM skills WHERE id = ?", (skill_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return dict(row)
        return None

    async def get_skill_by_name(self, name: str) -> Optional[dict]:
        """Get a skill by name."""
        async with self.conn.execute(
            "SELECT * FROM skills WHERE name = ?", (name,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return dict(row)
        return None

    async def update_skill(self, skill_id: str, **kwargs) -> Optional[dict]:
        """Update a skill record."""
        kwargs["updated_at"] = datetime.utcnow().isoformat()
        set_clause = ", ".join(f"{k} = ?" for k in kwargs)
        values = list(kwargs.values()) + [skill_id]

        await self.conn.execute(
            f"UPDATE skills SET {set_clause} WHERE id = ?", values
        )
        await self.conn.commit()
        return await self.get_skill(skill_id)

    async def delete_skill(self, skill_id: str) -> bool:
        """Delete a skill and its files."""
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
        """List skills with optional search and filtering."""
        conditions = []
        params = []

        if query:
            conditions.append(
                "(name LIKE ? OR display_name LIKE ? OR description LIKE ?)"
            )
            q = f"%{query}%"
            params.extend([q, q, q])

        if category:
            conditions.append("category = ?")
            params.append(category)

        where = " WHERE " + " AND ".join(conditions) if conditions else ""
        order = f" ORDER BY {sort} DESC" if sort else ""
        pagination = f" LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        async with self.conn.execute(
            f"SELECT * FROM skills{where}{order}{pagination}", params
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def count_skills(
        self, query: Optional[str] = None, category: Optional[str] = None
    ) -> int:
        """Count skills matching filters."""
        conditions = []
        params = []

        if query:
            conditions.append(
                "(name LIKE ? OR display_name LIKE ? OR description LIKE ?)"
            )
            q = f"%{query}%"
            params.extend([q, q, q])

        if category:
            conditions.append("category = ?")
            params.append(category)

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
        """Add a file record for a skill."""
        await self.conn.execute(
            """INSERT OR REPLACE INTO skill_files (skill_id, filename, content_type, size_bytes)
               VALUES (?, ?, ?, ?)""",
            (skill_id, filename, content_type, size_bytes),
        )
        await self.conn.commit()

    async def get_skill_files(self, skill_id: str) -> list[dict]:
        """Get all files for a skill."""
        async with self.conn.execute(
            "SELECT * FROM skill_files WHERE skill_id = ? ORDER BY filename",
            (skill_id,),
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def delete_skill_files(self, skill_id: str) -> None:
        """Delete all file records for a skill."""
        await self.conn.execute(
            "DELETE FROM skill_files WHERE skill_id = ?", (skill_id,)
        )
        await self.conn.commit()

    # --- API Tokens ---

    async def create_token(self, token_hash: str, owner_name: Optional[str] = None) -> dict:
        """Create an API token."""
        await self.conn.execute(
            "INSERT INTO api_tokens (token_hash, owner_name) VALUES (?, ?)",
            (token_hash, owner_name),
        )
        await self.conn.commit()
        async with self.conn.execute(
            "SELECT * FROM api_tokens WHERE token_hash = ?", (token_hash,)
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else {}

    async def validate_token(self, token_hash: str) -> Optional[dict]:
        """Validate an API token."""
        async with self.conn.execute(
            "SELECT * FROM api_tokens WHERE token_hash = ?", (token_hash,)
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def delete_token(self, token_id: int) -> bool:
        """Delete an API token."""
        async with self.conn.execute(
            "DELETE FROM api_tokens WHERE id = ?", (token_id,)
        ) as cursor:
            await self.conn.commit()
            return cursor.rowcount > 0

    async def list_tokens(self) -> list[dict]:
        """List all API tokens."""
        async with self.conn.execute(
            "SELECT * FROM api_tokens ORDER BY created_at DESC"
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
