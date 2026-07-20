"""List skills in the registry."""

import click
import httpx

from skillhub.config import load_config


@click.command(name="list")
@click.option("--category", "-c", help="Filter by category")
@click.option("--limit", "-n", default=50, help="Max results")
@click.option("--server", help="Override registry server URL")
def list_skills(category: str, limit: int, server: str):
    """List available skills in the registry."""
    config = load_config()
    registry_url = server or config.registry_url

    params = {"limit": limit}
    if category:
        params["category"] = category

    with httpx.Client(timeout=10.0) as client:
        response = client.get(f"{registry_url}/api/skills", params=params)

        if response.status_code != 200:
            click.echo(f"Error: Failed to list skills ({response.status_code})", err=True)
            raise SystemExit(1)

        skills = response.json()

        if not skills:
            click.echo("No skills in the registry yet.")
            return

        click.echo(f"Available skills ({len(skills)}):\n")

        # Group by category
        by_category = {}
        for skill in skills:
            cat = skill.get("category") or "uncategorized"
            by_category.setdefault(cat, []).append(skill)

        for cat, cat_skills in sorted(by_category.items()):
            click.echo(f"  [{cat}]")
            for skill in cat_skills:
                name = skill["name"]
                desc = skill.get("description", "")[:50]
                click.echo(f"    {name} - {desc}")
            click.echo()
