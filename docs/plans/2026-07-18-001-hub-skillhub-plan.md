# SkillHub - Plan

> **artifact_contract:** ce-unified-plan/v1
> **artifact_readiness:** implementation-ready
> **product_contract_source:** ce-brainstorm
> **created:** 2026-07-18
> **enriched:** 2026-07-18

---

## Goal

Build a lightweight, self-hosted skill registry for publishing and sharing Hermes Agent skills. Authors publish skills via CLI, anyone can browse and install via Web UI or CLI.

---

## Product Contract

### Primary Actors

- **Author** — skill creator who publishes skills to the registry via CLI
- **Consumer** — anyone who browses, searches, and installs skills via Web UI or CLI

### Core Outcome

A public skill registry where authors publish Hermes skills with one CLI command, and consumers discover and install skills with one CLI command or one click.

### In-Scope

1. **CLI Tool (`skillhub`)**
   - `skillhub push <path>` — publish a skill (SKILL.md + attachments) to the registry
   - `skillhub install <name>` — download and install a skill to `~/.hermes/skills/<category>/<name>/`
   - `skillhub search <query>` — search skills from the registry
   - `skillhub list` — list available skills
   - Auth via API token (generate with `skillhub auth login`)

2. **REST API**
   - `POST /api/skills` — publish a skill (authenticated)
   - `GET /api/skills` — list/search skills (public, with query params: q, category, sort)
   - `GET /api/skills/:id` — get skill detail
   - `GET /api/skills/:id/files/:filename` — download a skill file
   - `DELETE /api/skills/:id` — delete a skill (owner only)
   - SQLite database for metadata, local filesystem for skill files

3. **Web UI**
   - Browse skills by category
   - Search skills by keyword
   - View skill detail page (description, tags, author, files, install command)
   - One-click copy install command
   - Static SPA (React or vanilla JS), served by the same FastAPI server

4. **Skill Format**
   - Each skill is a directory containing `SKILL.md` (with YAML frontmatter) + optional reference files
   - Registry extracts metadata from SKILL.md frontmatter (name, description, category, tags)
   - Registry stores the full directory contents as downloadable files

### Out-of-Scope

- User registration/accounts (v1 uses API tokens generated manually)
- Skill versioning (v1: publish overwrites, no version history)
- Download counts, ratings, reviews, comments
- Private skill repositories
- CI/CD integration
- Multi-user RBAC or namespace governance
- Skill compatibility checking or validation beyond SKILL.md format

### Success Criteria

- Author can publish a skill from local machine with `skillhub push ./my-skill/`
- Consumer can install a skill with `skillhub install skill-name`
- Consumer can browse all skills at `http://localhost:8000`
- Consumer can search skills by keyword via Web UI or CLI
- Skill files (SKILL.md + references) are stored and served correctly

### Constraints

- Python stack: FastAPI + SQLite + Python CLI
- Single-machine deployment (no Docker required for MVP)
- Must work alongside existing `~/.hermes/skills/` without conflicts
- CLI tool should be installable via `pip install skillhub`

### Assumptions

- Users have Python 3.10+ installed
- The registry runs on a single machine initially (localhost or small VPS)
- Skill authors understand the SKILL.md format
- Public access is sufficient for v1 (no auth wall for browsing)

---

## High-Level Technical Design

### Architecture

```
┌─────────────┐     ┌──────────────────┐     ┌──────────────┐
│  CLI Tool   │────▶│   FastAPI Server  │────▶│   SQLite DB  │
│ (skillhub)  │     │   (REST API)      │     │  (metadata)  │
└─────────────┘     │                   │     └──────────────┘
                    │   Static Files    │
┌─────────────┐     │   (Web UI)        │     ┌──────────────┐
│   Browser   │────▶│                   │────▶│  Filesystem  │
│  (Web UI)   │     └──────────────────┘     │ (skill files)│
└─────────────┘                              └──────────────┘
```

### Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| Backend | FastAPI + uvicorn | Async, auto-docs, lightweight |
| Database | SQLite (via aiosqlite) | Zero-config, single-file, sufficient for MVP |
| File Storage | Local filesystem | Simple, no cloud dependency |
| Frontend | Vanilla HTML/CSS/JS | No build step, served by FastAPI |
| CLI | Click + httpx | Modern CLI framework, async HTTP |
| Validation | Pydantic v2 | Already used by FastAPI |

### Data Model

```sql
-- Skills table
CREATE TABLE skills (
    id TEXT PRIMARY KEY,           -- UUID
    name TEXT NOT NULL UNIQUE,     -- skill name (from frontmatter)
    display_name TEXT,             -- human-readable name
    description TEXT,
    category TEXT,
    tags TEXT,                     -- JSON array
    author TEXT,
    license TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    published_by TEXT              -- API token owner
);

-- Skill files table (tracks files uploaded per skill)
CREATE TABLE skill_files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    skill_id TEXT NOT NULL REFERENCES skills(id) ON DELETE CASCADE,
    filename TEXT NOT NULL,        -- relative path within skill dir
    content_type TEXT DEFAULT 'text/markdown',
    size_bytes INTEGER,
    UNIQUE(skill_id, filename)
);

-- API tokens
CREATE TABLE api_tokens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    token_hash TEXT NOT NULL UNIQUE,
    owner_name TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### File Storage Layout

```
~/.skillhub/
├── data/
│   └── skillhub.db          # SQLite database
├── skills/
│   ├── <skill-id-1>/        # one dir per skill
│   │   ├── SKILL.md
│   │   ├── references/
│   │   └── scripts/
│   └── <skill-id-2>/
│       └── ...
└── config.yaml              # server config
```

---

## Implementation Units

### U1: Project Scaffold & Data Layer

**Goal:** Set up project structure, database schema, and core data models.

**Files to create:**
- `pyproject.toml` — project metadata, dependencies
- `skillhub/__init__.py`
- `skillhub/models.py` — Pydantic models (Skill, SkillFile, ApiToken)
- `skillhub/database.py` — SQLite connection, migrations, CRUD helpers
- `skillhub/config.py` — config loading from ~/.skillhub/config.yaml
- `skillhub/storage.py` — file storage operations (save, retrieve, list)

**Dependencies:** None (foundational unit)

**Acceptance criteria:**
- Database initializes with schema on first run
- Can create, read, update, delete skill records
- Can save and retrieve skill files from filesystem
- Config loads from ~/.skillhub/config.yaml with sensible defaults

---

### U2: REST API

**Goal:** Implement all API endpoints for skill management.

**Files to create:**
- `skillhub/api/__init__.py`
- `skillhub/api/skills.py` — CRUD endpoints for skills
- `skillhub/api/auth.py` — token generation and validation
- `skillhub/api/deps.py` — dependency injection (db, auth)
- `skillhub/main.py` — FastAPI app, CORS, static file mount

**Endpoints:**

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | /api/skills | Yes | Publish/update a skill |
| GET | /api/skills | No | List/search skills |
| GET | /api/skills/{id} | No | Get skill detail |
| GET | /api/skills/{id}/files/{filename} | No | Download a file |
| DELETE | /api/skills/{id} | Yes | Delete a skill |
| POST | /api/auth/tokens | Yes | Generate API token |

**Dependencies:** U1

**Acceptance criteria:**
- All endpoints respond correctly
- Auth middleware validates tokens
- Search works via query param `q`
- File downloads serve correct content type
- API docs available at /docs (Swagger)

---

### U3: CLI Tool

**Goal:** Build the `skillhub` command-line tool.

**Files to create:**
- `skillhub/cli/__init__.py`
- `skillhub/cli/main.py` — Click app, command group
- `skillhub/cli/commands/push.py` — skillhub push
- `skillhub/cli/commands/install.py` — skillhub install
- `skillhub/cli/commands/search.py` — skillhub search
- `skillhub/cli/commands/list.py` — skillhub list
- `skillhub/cli/commands/auth.py` — skillhub auth

**Commands:**

```
skillhub push <path>              # publish skill from directory
skillhub install <name>           # install skill to ~/.hermes/skills/
skillhub search <query>           # search skills
skillhub list [--category X]      # list all skills
skillhub auth login               # configure API token
skillhub auth status              # show current token
```

**Dependencies:** U2 (needs API endpoints to talk to)

**Acceptance criteria:**
- `skillhub push ./my-skill/` parses SKILL.md, uploads files, creates/updates registry entry
- `skillhub install skill-name` downloads and places files in ~/.hermes/skills/<category>/<name>/
- `skillhub search python` returns matching skills
- `skillhub list` shows all available skills
- `skillhub auth login` prompts for server URL and token, saves to ~/.skillhub/config.yaml
- Clear error messages for network failures, missing files, auth errors

---

### U4: Web UI

**Goal:** Build the browser-based skill browser.

**Files to create:**
- `skillhub/static/index.html` — main page
- `skillhub/static/css/style.css` — styling
- `skillhub/static/js/app.js` — search, browse, detail view
- `skillhub/static/js/api.js` — API client

**Features:**
- Landing page with search bar and category filter
- Skill list grid/cards with name, description, category, tags
- Skill detail page with full description, file tree, install command
- One-click copy of install command (`skillhub install <name>`)
- Responsive design (works on mobile)

**Dependencies:** U2 (needs API endpoints)

**Acceptance criteria:**
- Page loads and shows skills from API
- Search filters skills in real-time
- Category filter works
- Skill detail page shows all metadata
- Install command is copyable with one click
- No JavaScript build step required

---

### U5: Integration & Packaging

**Goal:** End-to-end testing, packaging, and deployment readiness.

**Files to create:**
- `tests/test_api.py` — API endpoint tests
- `tests/test_cli.py` — CLI command tests
- `tests/test_models.py` — data model tests
- `Dockerfile` — optional Docker deployment
- `README.md` — setup and usage instructions

**Dependencies:** U1-U4

**Acceptance criteria:**
- `pip install -e .` installs the package
- `skillhub` command is available after install
- `uvicorn skillhub.main:app` starts the server
- All tests pass
- README explains setup, config, and usage
- Can push a skill and see it in the web UI
- Can install a skill and use it in Hermes

---

## Dependency Graph

```
U1 (Data Layer)
 ├──▶ U2 (REST API)
 │     ├──▶ U3 (CLI)
 │     └──▶ U4 (Web UI)
 └──▶ U5 (Integration) ← depends on U2, U3, U4
```

## Risks

1. **SKILL.md parsing** — YAML frontmatter varies across skills. Mitigation: use a lenient parser, handle missing fields gracefully.
2. **File conflicts on install** — `skillhub install` could overwrite existing skills in ~/.hermes/skills/. Mitigation: check for existing skill, prompt user or use `--force` flag.
3. **No auth for browse** — Public registry means anyone can see all skills. Acceptable for v1; add auth in v2 if needed.

---

## Outstanding Questions

1. **Deployment target** — Local machine for now; VPS or cloud later.
2. **Skill file size limits** — No limit for v1; add limits if abuse occurs.
3. **Categories** — Use Hermes category taxonomy (apple, creative, etc.) by default; allow custom categories via frontmatter.
