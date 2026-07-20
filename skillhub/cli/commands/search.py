"""Search skills in the registry."""

import click
import httpx

from skillhub.config import load_config


@click.command()
@click.argument("query")
@click.option("--category", "-c", help="Filter by category")
@click.option("--limit", "-n", default=20, help="Max results")
@click.option("--server", help="Override registry server URL")
def search(query: str, category: str, limit: int, server: str):
    """Search for skills in the registry."""
    config = load_config()
    registry_url = server or config.registry_url

    params = {"q": query, "limit": limit}
    if category:
        params["category"] = category

    with httpx.Client(timeout=10.0) as client:
        response = client.get(f"{registry_url}/api/skills", params=params)

        if response.status_code != 200:
            click.echo(f"Error: Failed to search ({response.status_code})", err=True)
            raise SystemExit(1)

        skills = response.json()

        if not skills:
            click.echo(f"No skills found for '{query}'")
            return

        click.echo(f"Found {len(skills)} skill(s):\n")

        for skill in skills:
            name = skill["name"]
            desc = skill.get("description", "No description")[:60]
            cat = skill.get("category", "")
            tags = skill.get("tags", [])

            click.echo(f"  {name}")
            click.echo(f"    {desc}")
            if cat:
                click.echo(f"    Category: {cat}")
            if tags:
                click.echo(f"    Tags: {', '.join(tags)}")
            click.echo()
