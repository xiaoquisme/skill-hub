# SkillHub

A lightweight, self-hosted skill registry for Hermes Agent skills.

## Quick Start (Server)

Deploy SkillHub with Docker:

```bash
git clone https://github.com/xiaoquisme/skillhub.git
cd skillhub
./quickstart.sh
```

Open http://localhost/ui/ in your browser.

### Or run locally

```bash
pip install -e .
uvicorn skillhub.main:app --reload
```

## Client CLI

Install the CLI to push and install skills from a SkillHub server:

```bash
pip install git+https://github.com/xiaoquisme/skillhub.git
```

### Configure the server

Create `~/.skillhub/config.yaml`:

```yaml
registry_url: http://<server-host>:80
```

### Usage

```bash
# Publish a skill
skillhub push ./my-skill/

# Install a skill
skillhub install skill-name

# Search skills
skillhub search keyword

# List available skills
skillhub list
```

## Configuration

Server configuration is stored in `~/.skillhub/config.yaml`:

```yaml
server:
  host: 127.0.0.1
  port: 8000
storage:
  data_dir: ~/.skillhub/data
  skills_dir: ~/.skillhub/skills
```

Environment variables override YAML values:

| Variable | Overrides |
|----------|-----------|
| `SKILLHUB_HOST` | `server.host` |
| `SKILLHUB_PORT` | `server.port` |
| `SKILLHUB_DATA_DIR` | `storage.data_dir` |
| `SKILLHUB_SKILLS_DIR` | `storage.skills_dir` |

## Development

```bash
pip install -e ".[dev]"
pytest
```

## License

MIT
