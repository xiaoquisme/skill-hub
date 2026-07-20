# SkillHub

A lightweight, self-hosted skill registry for Hermes Agent skills.

## Installation

```bash
pip install skillhub
```

## Quick Start

### Start the server

```bash
uvicorn skillhub.main:app --reload
```

### Publish a skill

```bash
skillhub auth login
skillhub push ./my-skill/
```

### Browse skills

Open http://localhost:8000 in your browser.

### Install a skill

```bash
skillhub install skill-name
```

## Configuration

Configuration is stored in `~/.skillhub/config.yaml`:

```yaml
server:
  host: 127.0.0.1
  port: 8000
storage:
  data_dir: ~/.skillhub/data
  skills_dir: ~/.skillhub/skills
```

## Development

```bash
pip install -e ".[dev]"
pytest
```

## License

MIT
