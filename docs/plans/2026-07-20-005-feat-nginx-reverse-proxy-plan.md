---
artifact_contract: ce-unified-plan/v1
artifact_readiness: implementation-ready
product_contract_source: ce-plan-bootstrap
created: 2026-07-20
type: feat
---

# Plan: Add nginx Reverse Proxy for SkillHub

## Goal Capsule

**Objective:** Add an nginx reverse proxy to the Docker Compose setup, routing external traffic to the SkillHub container.

**Authority:** ce-plan (direct invocation)

**Execution profile:** Lightweight — small, bounded, low ambiguity. 2 implementation units.

**Stop conditions:** nginx proxies HTTP requests to SkillHub, skillhub container is not directly exposed to host, docker compose up works end-to-end.

**Tail ownership:** User owns post-merge deployment decisions.

---

## Product Contract

### Problem Frame

SkillHub currently exposes port 8000 directly from the Python container. Adding nginx as a reverse proxy provides a standard entry point for production deployments, enables future features (SSL termination, rate limiting), and follows Docker best practices. The direct-port approach works for development but lacks the flexibility needed for production-like deployments where a proxy layer is expected.

### Requirements

- R1. nginx container added to docker-compose.yml
- R2. nginx proxies all traffic to skillhub:8000
- R3. nginx listens on a configurable port (default 80)
- R4. skillhub service no longer exposes port directly to host

### Scope Boundaries

**In scope:**
- nginx container and configuration
- docker-compose.yml updates
- quickstart.sh updates

**Out of scope:**
- SSL/TLS termination
- Rate limiting or access control
- Static file serving by nginx
- Multi-container load balancing

---

## Planning Contract

### Key Technical Decisions

**KTD1. Base image: nginx:alpine**
- Rationale: Lightweight, official image, minimal footprint; nginx is the most widely deployed reverse proxy
- Alternatives considered: Caddy (auto-SSL but heavier), Traefik (service discovery overkill for single-service), direct port exposure (no proxy benefits)

**KTD2. Configuration via mounted file**
- Rationale: Allows customization without rebuilding the image; follows 12-factor config pattern
- Alternative: Bake config into a custom image (adds build complexity)

### Assumptions

- Users have Docker and Docker Compose installed
- The existing SkillHub health check endpoint at `/api/health` remains available
- Port 80 is available on the host by default

---

## Implementation Units

### U1. Create nginx Configuration

**Goal:** Create an nginx configuration file that proxies requests to the SkillHub backend.

**Requirements:** R1, R2

**Dependencies:** None (foundational unit)

**Files:**
- `nginx.conf`

**Approach:**
- Create a minimal nginx config that proxies all requests to `skillhub:8000`
- Include proxy headers for proper request forwarding
- Configure upstream health check

**Technical design:**
```nginx
upstream skillhub {
    server skillhub:8000;
}

server {
    listen ${SKILLHUB_PORT:-80};
    server_name _;

    location / {
        proxy_pass http://skillhub;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 5s;
        proxy_read_timeout 30s;
    }

    location /api/health {
        proxy_pass http://skillhub;
        access_log off;
    }
}
```

**Test scenarios:**
- Happy path: nginx config file exists and is valid nginx syntax
- Happy path: config proxies to correct upstream (skillhub:8000)
- Edge case: config handles both / and /api/health paths

**Verification:**
- `nginx -t` validates config syntax (can be tested in container)

---

### U2. Update Docker Compose and Quickstart

**Goal:** Add nginx service to docker-compose.yml and update quickstart.sh.

**Requirements:** R1, R3, R4

**Dependencies:** U1

**Files:**
- `docker-compose.yml`
- `quickstart.sh`

**Approach:**
- Add nginx service to docker-compose.yml with port mapping and depends_on skillhub
- Remove direct port exposure from skillhub service
- Mount nginx.conf as a volume
- Update quickstart.sh to reflect new port (80 instead of 8000)

**Test scenarios:**
- Happy path: `docker compose up` starts both containers
- Happy path: curl to port 80 returns SkillHub response
- Happy path: skillhub container not directly accessible from host
- Edge case: SKILLHUB_PORT env var now controls nginx port
- Error case: nginx returns 502 when skillhub container is stopped

**Verification:**
- `docker compose up -d` starts successfully
- `curl http://localhost:80/api/health` returns `{"status":"ok"}`
- `docker compose ps` shows both nginx and skillhub running

---

## Verification Contract

| Command | Applicable Units | Pass Signal |
|---------|------------------|-------------|
| `docker compose up -d` | U1, U2 | Both containers start |
| `curl http://localhost:80/api/health` | U1, U2 | Returns health response |
| `docker compose down` | U2 | Clean shutdown |

---

## Definition of Done

- [ ] nginx.conf created with valid proxy configuration
- [ ] docker-compose.yml includes nginx service
- [ ] skillhub no longer exposes port directly to host
- [ ] quickstart.sh updated for new port
- [ ] `docker compose up` works end-to-end
- [ ] Health check accessible through nginx
