# feat: Add SkillHub documentation skills

**Date:** 2026-07-21
**Author:** Hermes Agent
**Plan type:** feat
**Plan depth:** Lightweight

---

## Summary

Create two Hermes-compatible skills under `skills/` in the skillhub repo that document the project's client CLI usage and server deployment procedures. These skills live in the repo as reference material — they are not installed into Hermes automatically, but serve as canonical documentation that can be published or distributed alongside the project.

## Problem Frame

The skillhub project has a README with basic usage instructions, but no structured Hermes skill format documentation. Creating skills in the standard Hermes format makes the documentation discoverable, reusable, and consistent with the Hermes ecosystem.

## Requirements

- Two SKILL.md files following the Hermes skill format (YAML frontmatter + markdown body)
- Client skill covers: installation, configuration, push, install, search, list commands
- Server skill covers: Docker deployment, local deployment, nginx reverse proxy, configuration
- Both skills use repo-relative references where applicable

## Implementation Units

### U1. Create client usage guide skill

**Goal:** Document the skillhub CLI commands and configuration for end users.

**Dependencies:** None

**Files:**
- `skills/skillhub-client/SKILL.md`

**Approach:**
Create a Hermes skill that documents the `skillhub` CLI tool. The skill should cover:
- Installation of the CLI (`pip install git+...`)
- Server configuration (`~/.skillhub/config.yaml`)
- CLI commands: `push`, `install`, `search`, `list`
- Each command's flags and options
- Common workflows (publish a skill, browse and install)

**Test expectation:** none — documentation-only, no behavioral changes

---

### U2. Create server deployment guide skill

**Goal:** Document how to deploy the SkillHub server via Docker or locally.

**Dependencies:** None

**Files:**
- `skills/skillhub-server/SKILL.md`

**Approach:**
Create a Hermes skill that documents server deployment. The skill should cover:
- Docker deployment (docker compose up)
- Local development (pip install + uvicorn)
- Nginx reverse proxy configuration
- Environment variables and config overrides
- Health check endpoint
- Web UI and API docs URLs

**Test expectation:** none — documentation-only, no behavioral changes

---

## Scope Boundaries

**In scope:**
- Two SKILL.md files in `skills/` directory
- CLI usage documentation
- Server deployment documentation

**Out of scope:**
- Auto-installation of skills into Hermes
- CI/CD for skill publishing
- Changes to the skillhub application code

## Definition of Done

- `skills/skillhub-client/SKILL.md` exists with complete CLI documentation
- `skills/skillhub-server/SKILL.md` exists with complete deployment documentation
- Both follow Hermes skill format (YAML frontmatter with name, description, tags)
