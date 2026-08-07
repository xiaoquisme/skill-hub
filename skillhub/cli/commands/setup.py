"""Setup CLI command - configure admin account."""

import click
import bcrypt
from skillhub.config import load_config, save_config, CONFIG_FILE


@click.command()
@click.option("--username", default=None, help="Admin username (default: admin)")
@click.option("--password", default=None, help="Admin password (will prompt if omitted)")
@click.option("--output", type=click.Path(), default=None,
              help="Write to a specific file instead of ~/.skillhub/config.yaml")
def setup(username, password, output):
    """Set up the default admin account.

    Writes admin credentials to ~/.skillhub/config.yaml.
    On next server start, the admin user is auto-created in the database.
    """
    config = load_config()

    # Username
    if username is None:
        username = click.prompt("Admin username", default=config.admin.username or "admin")
    if not username.strip():
        click.echo("Error: username cannot be empty", err=True)
        raise SystemExit(1)

    # Password
    if password is None:
        click.echo("Enter the admin password (input hidden):")
        password = click.prompt("Password", hide_input=True, confirmation_prompt=True)

    if not password:
        click.echo("Error: password cannot be empty", err=True)
        raise SystemExit(1)

    # Hash
    password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    # Update config
    config.admin.username = username
    config.admin.password_hash = password_hash

    if output:
        from pathlib import Path
        out_path = Path(output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        save_config(config, config_path=out_path)
        click.echo(f"Admin account configured.")
        click.echo(f"  Username:  {username}")
        click.echo(f"  Config:    {out_path}")
        click.echo()
        click.echo(f"scp {out_path} user@server:~/.skillhub/config.yaml")
    else:
        save_config(config)
        click.echo(f"Admin account configured.")
        click.echo(f"  Username:  {username}")
        click.echo(f"  Config:    {CONFIG_FILE}")
        click.echo()
        click.echo("Start the server with 'skillhub serve' to apply.")
