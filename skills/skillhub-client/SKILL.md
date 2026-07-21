---
name: skillhub-client
description: "Use the SkillHub CLI to publish, search, install, and manage Hermes Agent skills from a self-hosted registry."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [skills, registry, skillhub, cli, hermes]
---

# SkillHub Client CLI

Use the `skillhub` CLI to publish, search, install, and manage Hermes Agent skills from a self-hosted SkillHub registry.

## Trigger

Use this skill when:
- User wants to publish a skill to a SkillHub registry
- User wants to install skills from a SkillHub registry
- User wants to search or browse available skills
- User asks about SkillHub CLI commands or configuration

## Installation

Install the SkillHub CLI from the GitHub repo:

```bash
uv tool install git+https://github.com/xiaoquisme/skill-hub.git
```

After installation, the `skillhub` command is available globally.

## Configure the Server

Create `~/.skillhub/config.yaml` to point at your registry:

```yaml
registry_url: http://<server-host>:80
```

Default is `http://127.0.0.1:8000` if no config file exists.

You can override the server URL per-command with `--server`:

```bash
skillhub --server http://other-server:8000 list
```

## Commands

### skillhub push

Publish a skill directory to the registry.

```bash
skillhub push ./my-skill/
```

The directory must contain a `SKILL.md` file. Metadata (name, description, category, tags, author, license) is extracted from the SKILL.md frontmatter.

**Options:**
- `--force` — overwrite an existing skill with the same name
- `--server URL` — override the registry server

**What happens:**
1. Parses `SKILL.md` frontmatter for metadata
2. Collects all files in the directory (excluding dotfiles)
3. Uploads metadata + files to the registry
4. If the skill name already exists, updates it; otherwise creates a new entry

### skillhub install

Install a skill from the registry to `~/.hermes/skills/`.

```bash
skillhub install skill-name
```

**Options:**
- `--category, -c` — install into a specific category subdirectory
- `--server URL` — override the registry server

**What happens:**
1. Searches the registry for the skill by name
2. Downloads all skill files
3. Installs to `~/.hermes/skills/<category>/<name>/`
4. Prompts before overwriting if skill already exists

After installation, use the skill in Hermes:
```
/skill skill-name
```

### skillhub search

Search for skills in the registry.

```bash
skillhub search keyword
```

**Options:**
- `--category, -c` — filter by category
- `--limit, -n` — max results (default: 20)
- `--server URL` — override the registry server

### skillhub list

List all available skills in the registry.

```bash
skillhub list
```

**Options:**
- `--category, -c` — filter by category
- `--limit, -n` — max results (default: 50)
- `--server URL` — override the registry server

Skills are grouped by category in the output.

## Common Workflows

### Publish a new skill

```bash
# 1. Create your skill directory with SKILL.md
mkdir my-skill && cd my-skill
# ... write SKILL.md and other files ...

# 2. Publish to the registry
skillhub push .

# 3. Verify it's published
skillhub search my-skill
```

### Browse and install skills

```bash
# List all available skills
skillhub list

# Search for specific functionality
skillhub search docker

# Install a skill
skillhub install docker
```

### Update a published skill

```bash
# Just push again — it updates the existing entry
skillhub push ./my-skill/ --force
```

## Pitfalls

- **SKILL.md is required** — `push` fails without it. The `name` field in frontmatter determines the published name; if missing, the directory name is used.
- **Overwrite prompts** — `install` asks before overwriting an existing skill. Use `--force` on push to skip the prompt for updates.
- **Dotfiles excluded** — files starting with `.` are not uploaded during push.
- **Config location** — `~/.skillhub/config.yaml` is the default. Create it if it doesn't exist.

## Verification

After setup, verify the CLI works:

```bash
skillhub --version
skillhub list
```

If `list` returns "No skills in the registry yet." — the CLI is connected and working.
