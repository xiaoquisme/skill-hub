"""Push (publish) a skill to the registry."""

import json
from pathlib import Path

import click
import httpx
import yaml

from skillhub.config import load_config


def parse_skill_md(path: Path) -> dict:
    """Parse SKILL.md frontmatter to extract metadata."""
    skill_md = path / "SKILL.md"
    if not skill_md.exists():
        click.echo(f"Error: No SKILL.md found in {path}", err=True)
        raise SystemExit(1)

    content = skill_md.read_text()
    if not content.startswith("---"):
        return {"name": path.name}

    parts = content.split("---", 2)
    if len(parts) < 3:
        return {"name": path.name}

    try:
        frontmatter = yaml.safe_load(parts[1])
        return frontmatter if isinstance(frontmatter, dict) else {"name": path.name}
    except yaml.YAMLError:
        return {"name": path.name}


def collect_files(path: Path) -> list[tuple[str, bytes]]:
    """Collect all files in the skill directory."""
    files = []
    for file_path in path.rglob("*"):
        if file_path.is_file() and not file_path.name.startswith("."):
            rel = file_path.relative_to(path)
            files.append((str(rel), file_path.read_bytes()))
    return files


@click.command()
@click.argument("path", type=click.Path(exists=True, path_type=Path))
@click.option("--force", is_flag=True, help="Overwrite existing skill")
@click.option("--server", help="Override registry server URL")
def push(path: Path, force: bool, server: str):
    """Publish a skill to the registry.

    PATH is the directory containing SKILL.md and skill files.
    """
    config = load_config()
    registry_url = server or config.registry_url

    if not config.api_token:
        click.echo("Error: Not authenticated. Run 'skillhub auth login' first.", err=True)
        raise SystemExit(1)

    # Parse skill metadata
    metadata = parse_skill_md(path)
    name = metadata.get("name", path.name)

    click.echo(f"Publishing skill: {name}")

    # Collect files
    files = collect_files(path)
    click.echo(f"  Files: {len(files)}")

    # Upload to registry
    headers = {"Authorization": f"Bearer {config.api_token}"}

    with httpx.Client(timeout=30.0) as client:
        # Prepare multipart form data
        data = {
            "name": name,
            "display_name": metadata.get("display_name", ""),
            "description": metadata.get("description", ""),
            "category": metadata.get("category", ""),
            "tags": json.dumps(metadata.get("tags", [])),
            "author": metadata.get("author", ""),
            "license": metadata.get("license", ""),
        }

        upload_files = []
        for filename, content in files:
            upload_files.append(("files", (filename, content, "application/octet-stream")))

        response = client.post(
            f"{registry_url}/api/skills",
            headers=headers,
            data=data,
            files=upload_files,
        )

        if response.status_code == 201:
            skill = response.json()
            click.echo(f"  Published: {skill['name']} (id: {skill['id'][:8]}...)")
        elif response.status_code == 401:
            click.echo("Error: Authentication failed. Check your API token.", err=True)
            raise SystemExit(1)
        else:
            click.echo(f"Error: {response.status_code} - {response.text}", err=True)
            raise SystemExit(1)
