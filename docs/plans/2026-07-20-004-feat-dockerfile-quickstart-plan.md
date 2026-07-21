---
artifact_contract: ce-unified-plan/v1
artifact_readiness: implementation-ready
product_contract_source: ce-plan-bootstrap
created: 2026-07-20
type: feat
---

# Plan: Dockerfile and Quick Start Script for SkillHub

## Goal Capsule

**Objective:** Create a Dockerfile and quick start script that enables easy setup and deployment of SkillHub on any machine with Docker installed.

**Authority:** ce-plan (direct invocation)

**Execution profile:** Lightweight — small, bounded, low ambiguity. 2-3 implementation units.

**Stop conditions:** Dockerfile builds successfully, quick start script runs without errors, container serves the SkillHub application on the expected port.

**Tail ownership:** User owns post-merge verification and deployment decisions.

---

## Product Contract

### Problem Frame

SkillHub is a Python FastAPI application that serves as a skill registry for Hermes Agent skills. Currently, setup requires manual Python environment configuration, virtualenv creation, and dependency installation. Users want to deploy SkillHub on other machines quickly without environment-specific setup.

### Requirements

- R1. Dockerfile must build a working SkillHub container with all dependencies
- R2. Quick start script must automate Docker build and run process
- R3. Container must expose the web UI on port 8000
- R4. Data persistence must work across container restarts (volume mounts)
- R5. Script must work on macOS, Linux, and Windows (with Docker Desktop)

### Scope Boundaries

**In scope:**
- Dockerfile for the SkillHub application
- Quick start shell script (build + run)
- docker-compose.yml for easy orchestration
- Volume mounting for data persistence
- Environment variable configuration

**Out of scope:**
- Production deployment hardening (reverse proxy, SSL, etc.)
- CI/CD pipeline for automated builds
- Multi-stage builds for optimization (can be added later)
- Kubernetes or cloud-specific deployment

---

## Planning Contract

### Key Technical Decisions

**KTD1. Base image: python:3.11-slim**
- Rationale: Lightweight, official Python image, matches project's Python 3.10+ requirement
- Alternative: python:3.11-alpine (smaller but may have compatibility issues with some packages)

**KTD2. Dependency installation: pip with pyproject.toml**
- Rationale: Standard Python packaging, compatible with pyproject.toml
- Alternative: pip-tools or poetry (adds complexity for a simple deployment)

**KTD3. Quick start script: bash with docker compose**
- Rationale: Simple, cross-platform with Docker Desktop, easy to understand
- Alternative: Docker-only commands (more manual but fewer dependencies)

### Assumptions

- Users have Docker and Docker Compose installed
- Users want a single-command setup experience
- Data persistence is important (skills and database should survive restarts)
- Default configuration is sufficient for initial setup

### Sequencing

1. Create Dockerfile (U1)
2. Create docker-compose.yml and quick start script (U2)

---

## Implementation Units

### U1. Dockerfile

**Goal:** Create a Dockerfile that builds a working SkillHub container.

**Requirements:** R1, R3, R4

**Dependencies:** None (foundational unit)

**Files:**
- `Dockerfile`
- `.dockerignore`

**Approach:**
- Use python:3.11-slim as base image
- Install system dependencies (if any)
- Copy pyproject.toml and skillhub/ package, then install Python dependencies
- Create non-root user for security
- Expose port 8000
- Set entrypoint to run uvicorn

**Technical design:**
```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy source code and install dependencies
COPY pyproject.toml .
COPY skillhub/ skillhub/
RUN pip install --no-cache-dir .

# Create data directories
RUN mkdir -p /data/skills /data/db

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app /data
USER appuser

# Expose port
EXPOSE 8000

# Environment variables
ENV SKILLHUB_DATA_DIR=/data/db
ENV SKILLHUB_SKILLS_DIR=/data/skills

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health')" || exit 1

# Run the application
CMD ["uvicorn", "skillhub.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Test scenarios:**
- Happy path: Docker image builds without errors
- Happy path: Container starts and serves the web UI on port 8000
- Happy path: Health check endpoint returns OK
- Edge case: Container runs as non-root user
- Edge case: Data directories are created with correct permissions

**Verification:**
- `docker build -t skillhub .` completes successfully
- `docker run -p 8000:8000 skillhub` starts and serves the web UI
- `curl http://localhost:8000/api/health` returns `{"status": "ok"}`

---

### U2. Docker Compose and Quick Start Script

**Goal:** Create docker-compose.yml and a quick start script for easy setup.

**Requirements:** R2, R3, R4, R5

**Dependencies:** U1

**Files:**
- `docker-compose.yml`
- `quickstart.sh`

**Approach:**
- Create docker-compose.yml with service definition, volume mounts, and environment variables
- Create quickstart.sh that checks Docker availability, builds the image, and starts the container
- Support environment variable overrides for customization
- Include helpful output messages for user guidance

**Technical design:**
```yaml
# docker-compose.yml
version: '3.8'

services:
  skillhub:
    build: .
    ports:
      - "${SKILLHUB_PORT:-8000}:8000"
    volumes:
      - skillhub-data:/data/db
      - skillhub-skills:/data/skills
    environment:
      - SKILLHUB_HOST=${SKILLHUB_HOST:-0.0.0.0}
    restart: unless-stopped

volumes:
  skillhub-data:
  skillhub-skills:
```

```bash
#!/bin/bash
# quickstart.sh

set -e

echo "SkillHub Quick Start"
echo "==================="

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed."
    echo "Please install Docker from https://docs.docker.com/get-docker/"
    exit 1
fi

if ! docker info &> /dev/null; then
    echo "Error: Docker daemon is not running."
    echo "Please start Docker and try again."
    exit 1
fi

# Check Docker Compose
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "Error: Docker Compose is not installed."
    echo "Please install Docker Compose or Docker Desktop."
    exit 1
fi

# Build and run
echo "Building SkillHub image..."
docker compose build

echo ""
echo "Starting SkillHub..."
docker compose up -d

# Wait for service to be ready
echo "Waiting for SkillHub to be ready..."
PORT="${SKILLHUB_PORT:-8000}"
RETRIES=0
MAX_RETRIES=30
while [ $RETRIES -lt $MAX_RETRIES ]; do
    if curl -sf "http://localhost:${PORT}/api/health" > /dev/null 2>&1; then
        break
    fi
    RETRIES=$((RETRIES + 1))
    sleep 1
done

if [ $RETRIES -eq $MAX_RETRIES ]; then
    echo "Warning: SkillHub may not be ready yet. Check logs with: docker compose logs"
else
    echo "SkillHub is ready!"
fi

echo ""
echo "Web UI: http://localhost:${PORT}"
echo "API docs: http://localhost:${PORT}/docs"
echo ""
echo "To stop: docker compose down"
echo "To view logs: docker compose logs -f"
```

**Test scenarios:**
- Happy path: quickstart.sh runs without errors on a machine with Docker
- Happy path: docker-compose.yml starts SkillHub and exposes port 8000
- Happy path: Data persists after container restart
- Edge case: Script provides clear error message when Docker is not installed
- Edge case: Script provides clear error message when Docker daemon is not running

**Verification:**
- `./quickstart.sh` builds and starts SkillHub successfully
- Web UI is accessible at http://localhost:8000
- Data persists after `docker compose down && docker compose up -d`
- `docker compose logs` shows no errors

---

## Verification Contract

| Command | Applicable Units | Pass Signal |
|---------|------------------|-------------|
| `docker build -t skillhub .` | U1 | Image builds successfully |
| `docker run -p 8000:8000 skillhub` | U1 | Container starts, health check passes |
| `./quickstart.sh` | U2 | SkillHub starts, web UI accessible |
| `docker compose up -d` | U2 | Container starts, data persists |

---

## Definition of Done

- [ ] Dockerfile builds successfully
- [ ] Container runs and serves the web UI
- [ ] Health check endpoint works
- [ ] docker-compose.yml works with volume mounts
- [ ] quickstart.sh automates the entire setup process
- [ ] Data persists across container restarts
- [ ] Script works on macOS, Linux, and Windows (with Docker Desktop)
