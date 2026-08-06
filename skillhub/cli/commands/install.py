"""Install a skill from the registry."""

from pathlib import Path

import click
import httpx

from skillhub.config import load_config
from skillhub.targets import registry, TargetScope


@click.command()
@click.argument("name")
@click.option("--target", "-t", default=None, help="Target platform (hermes, claude-code, codex)")
@click.option("--scope", "-s", default=None, type=click.Choice(["user", "project"]), help="Installation scope")
@click.option("--category", "-c", default=None, help="Category subdirectory (Hermes only)")
@click.option("--server", default=None, help="Override registry server URL")
@click.option("--yes", "-y", is_flag=True, default=False, help="Auto-confirm overwrites")
def install(name: str, target: str, scope: str, category: str, server: str, yes: bool):
    """Install a skill from the registry to a target platform directory."""
    config = load_config()
    registry_url = server or config.registry_url

    # Resolve target from config default if not specified
    if target is None:
        target = next(iter(config.targets.keys()), "hermes")

    # Resolve scope from config default if not specified
    if scope is None:
        target_config = config.targets.get(target)
        scope = target_config.scope if target_config else "user"

    # Get adapter
    try:
        adapter = registry.get_or_raise(target)
    except KeyError as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)

    scope_enum = TargetScope(scope)

    # Warn if --category used with non-Hermes target
    if category and target != "hermes":
        click.echo(f"Warning: --category is ignored for target '{target}'", err=True)

    click.echo(f"Installing skill: {name} -> {adapter.description} ({scope} scope)")

    with httpx.Client(timeout=30.0) as client:
        # Search for the skill by name
        response = client.get(
            f"{registry_url}/api/skills",
            params={"q": name},
        )

        if response.status_code != 200:
            click.echo(f"Error: Failed to search skills ({response.status_code})", err=True)
            raise SystemExit(1)

        skills = response.json()
        if not skills:
            click.echo(f"Error: Skill '{name}' not found", err=True)
            raise SystemExit(1)

        # Find exact match
        skill = None
        for s in skills:
            if s["name"] == name:
                skill = s
                break

        if not skill:
            skill = skills[0]
            click.echo(f"  Using closest match: {skill['name']}")

        skill_id = skill["id"]
        skill_name = skill["name"]
        skill_category = skill.get("category") or category

        # Get skill details
        response = client.get(f"{registry_url}/api/skills/{skill_id}")
        if response.status_code != 200:
            click.echo("Error: Failed to get skill details", err=True)
            raise SystemExit(1)

        detail = response.json()

        # Resolve install path using target adapter
        install_dir = adapter.resolve_path(skill_name, scope_enum, skill_category)

        if install_dir.exists():
            click.echo(f"  Skill already exists at {install_dir}")
            if not yes and not click.confirm("Overwrite?"):
                click.echo("Aborted.")
                return

        # Download all files
        files_data = {}
        files = detail.get("files", [])
        click.echo(f"  Files: {len(files)}")

        for file_info in files:
            filename = file_info["filename"]
            response = client.get(
                f"{registry_url}/api/skills/{skill_id}/files/{filename}"
            )

            if response.status_code == 200:
                files_data[filename] = response.content
                click.echo(f"    {filename}")
            else:
                click.echo(f"    Warning: Failed to download {filename}", err=True)

        # Write files using target adapter
        if files_data:
            written = adapter.write_skill(install_dir, files_data)
            click.echo(f"\nInstalled {skill_name} to {install_dir}")
        else:
            click.echo("\nWarning: No files were downloaded", err=True)
            raise SystemExit(1)
