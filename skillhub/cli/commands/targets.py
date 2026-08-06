"""List available installation targets."""

import click

from skillhub.config import load_config
from skillhub.targets import registry


@click.command()
def targets():
    """Show available installation targets and their configured paths."""
    config = load_config()

    click.echo("Available installation targets:\n")
    click.echo(f"{'Target':<15} {'Description':<25} {'Default Scope':<15} {'Enabled':<10}")
    click.echo("-" * 65)

    for adapter in registry.list_all():
        target_config = config.targets.get(adapter.name)
        scope = target_config.scope if target_config else "user"
        enabled = target_config.enabled if target_config else True
        enabled_str = "yes" if enabled else "no"
        click.echo(f"{adapter.name:<15} {adapter.description:<25} {scope:<15} {enabled_str:<10}")

    # Show default target
    default_target = next(iter(config.targets.keys()), "hermes")
    click.echo(f"\nDefault target: {default_target}")
