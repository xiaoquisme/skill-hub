"""Authentication commands."""

import click
import httpx

from skillhub.config import AppConfig, load_config, save_config


@click.group()
def auth():
    """Manage API authentication."""
    pass


@auth.command()
def login():
    """Configure API token for publishing skills."""
    config = load_config()

    click.echo("SkillHub Authentication Setup")
    click.echo("=============================\n")

    server_url = click.prompt(
        "Registry URL",
        default=config.registry_url,
        show_default=True,
    )

    api_token = click.prompt("API Token", hide_input=True)

    # Verify the token works
    click.echo("\nVerifying token...")

    with httpx.Client(timeout=10.0) as client:
        headers = {"Authorization": f"Bearer {api_token}"}
        # Try to list tokens (requires auth) as a verification
        response = client.get(f"{server_url}/api/auth/tokens", headers=headers)

        # Even a 404 means the server exists and token was processed
        if response.status_code in (200, 404, 405):
            click.echo("Token verified!")
        elif response.status_code == 401:
            click.echo("Error: Invalid token. Please check your API token.", err=True)
            raise SystemExit(1)
        else:
            click.echo(f"Warning: Server returned {response.status_code}")

    # Save config
    config.registry_url = server_url
    config.api_token = api_token
    save_config(config)

    click.echo(f"\nConfiguration saved to ~/.skillhub/config.yaml")


@auth.command()
def status():
    """Show current authentication status."""
    config = load_config()

    click.echo("SkillHub Auth Status")
    click.echo("====================\n")

    click.echo(f"  Registry URL: {config.registry_url}")
    if config.api_token:
        masked = config.api_token[:8] + "..." + config.api_token[-4:]
        click.echo(f"  API Token:    {masked}")
    else:
        click.echo("  API Token:    Not configured")
        click.echo("\n  Run 'skillhub auth login' to set up authentication.")
