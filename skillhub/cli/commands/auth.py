"""Auth CLI commands - login, logout, status."""

import click
import httpx
from skillhub.config import load_config, save_config, CONFIG_FILE


@click.group()
def auth():
    """Manage authentication with the SkillHub registry."""
    pass


@auth.command()
@click.option("--server", help="Override registry server URL")
def login(server: str):
    """Login to the SkillHub registry."""
    config = load_config()
    registry_url = server or config.registry_url

    username = click.prompt("Username")
    password = click.prompt("Password", hide_input=True)

    with httpx.Client(timeout=10.0) as client:
        response = client.post(
            f"{registry_url}/api/auth/login",
            json={"username": username, "password": password},
        )

        if response.status_code == 200:
            data = response.json()
            config.api_token = data["access_token"]
            save_config(config)
            click.echo(f"Logged in as {username}")
        else:
            click.echo(f"Login failed: {response.status_code} - {response.text}", err=True)
            raise SystemExit(1)


@auth.command()
def logout():
    """Logout from the SkillHub registry."""
    config = load_config()
    config.api_token = ""
    save_config(config)
    click.echo("Logged out successfully")


@auth.command()
def status():
    """Show current authentication status."""
    config = load_config()
    if config.api_token:
        click.echo("Status: Logged in")
        # Try to decode the token to show user info
        try:
            from skillhub.auth import decode_token
            payload = decode_token(config.api_token)
            click.echo(f"  User ID: {payload.get('user_id', 'unknown')}")
            click.echo(f"  Role: {payload.get('role', 'unknown')}")
        except Exception:
            click.echo("  (Could not decode token details)")
    else:
        click.echo("Status: Not logged in")
        click.echo("  Run 'skillhub auth login' to authenticate")
