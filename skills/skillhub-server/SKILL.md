---
name: skillhub-server
description: "Deploy and configure a self-hosted SkillHub server for Hermes Agent skill management."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [skills, registry, skillhub, server, docker, deployment]
---

# SkillHub Server Deployment

Deploy a self-hosted SkillHub server to manage Hermes Agent skills. SkillHub is a lightweight FastAPI application with SQLite storage and a built-in web UI.

## Trigger

Use this skill when:
- User wants to deploy a SkillHub server
- User asks about SkillHub server configuration
- User needs to set up Docker or local deployment
- User asks about nginx reverse proxy for SkillHub

## Prerequisites

- Python 3.10+ (for local deployment)
- Docker + Docker Compose (for container deployment)
- Network access between clients and the server

## Quick Start (Docker)

The fastest way to get running:

```bash
git clone https://github.com/xiaoquisme/skillhub.git
cd skillhub
./quickstart.sh
```

This builds the Docker image, starts SkillHub with nginx, and waits for readiness.

Access:
- Web UI: `http://localhost/ui/`
- API docs: `http://localhost/docs`

To stop:
```bash
docker compose down
```

## Docker Compose Deployment

The `docker-compose.yml` runs two services:

1. **skillhub** — the FastAPI application (internal port 8000)
2. **nginx** — reverse proxy (external port 80, configurable via `SKILLHUB_PORT`)

```bash
# Start
docker compose up -d

# Check status
docker compose ps

# View logs
docker compose logs -f

# Stop
docker compose down
```

**Custom port:**
```bash
SKILLHUB_PORT=8080 docker compose up -d
```

**Persistent data:**
Docker volumes `skillhub-data` and `skillhub-skills` persist the database and skill files across restarts.

## Local Development

Run without Docker:

```bash
# Clone and install
git clone https://github.com/xiaoquisme/skillhub.git
cd skillhub
pip install -e .

# Start the server
uvicorn skillhub.main:app --reload
```

Server runs at `http://127.0.0.1:8000` by default.

Web UI: `http://127.0.0.1:8000/ui/`
API docs: `http://127.0.0.1:8000/docs`

## Configuration

Server configuration is stored in `~/.skillhub/config.yaml`:

```yaml
server:
  host: 127.0.0.1
  port: 8000
  debug: false
storage:
  data_dir: ~/.skillhub/data
  skills_dir: ~/.skillhub/skills
```

### Environment Variables

Environment variables override YAML values (useful for Docker):

| Variable | Overrides | Default |
|----------|-----------|---------|
| `SKILLHUB_HOST` | `server.host` | `127.0.0.1` |
| `SKILLHUB_PORT` | `server.port` | `8000` |
| `SKILLHUB_DATA_DIR` | `storage.data_dir` | `~/.skillhub/data` |
| `SKILLHUB_SKILLS_DIR` | `storage.skills_dir` | `~/.skillhub/skills` |

## Nginx Reverse Proxy

For production, put SkillHub behind nginx. The included `nginx.conf` provides:

- Reverse proxy to the SkillHub backend
- Health check endpoint (`/api/health`) with access logging disabled
- Standard proxy headers (X-Real-IP, X-Forwarded-For, X-Forwarded-Proto)
- Timeouts: 5s connect, 30s read

To use with Docker Compose, the nginx service is already included. For standalone nginx:

```bash
# Copy the config
cp nginx.conf /etc/nginx/conf.d/skillhub.conf

# Edit upstream server if needed
# Reload nginx
nginx -s reload
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/health` | Health check |
| `GET` | `/api/skills` | List/search skills |
| `GET` | `/api/skills/{id}` | Get skill details |
| `GET` | `/api/skills/{id}/files/{name}` | Download a skill file |
| `POST` | `/api/skills` | Publish/update a skill |
| `DELETE` | `/api/skills/{id}` | Delete a skill |

**Query parameters for list endpoint:**
- `q` — search query (matches name/description)
- `category` — filter by category
- `sort` — sort field (default: `updated_at`)
- `limit` — max results (1-100, default: 50)
- `offset` — pagination offset

## Health Check

The server exposes a health endpoint at `/api/health`:

```bash
curl http://localhost:8000/api/health
# {"status": "ok", "service": "skillhub"}
```

Docker healthcheck polls this every 30 seconds.

## Pitfalls

- **Port conflicts** — if port 80 or 8000 is in use, change `SKILLHUB_PORT` or the `server.port` config.
- **Data persistence** — Docker volumes persist data, but `docker compose down -v` removes them. Use `docker compose down` (without `-v`) to keep data.
- **CORS** — the server allows all origins by default (`allow_origins=["*"]`). For production, restrict this in `main.py`.
- **SQLite limitations** — the default database is SQLite, suitable for single-server deployments. For multi-server setups, consider switching the database backend.

## Verification

After deployment, verify the server is running:

```bash
# Health check
curl http://localhost:8000/api/health

# List skills (should return empty array or skills)
curl http://localhost:8000/api/skills

# Open web UI
open http://localhost/ui/
```
