"""SkillHub CLI - publish and install Hermes Agent skills."""

import click

from skillhub import __version__


@click.group()
@click.version_option(__version__, prog_name="skillhub")
def cli():
    """SkillHub - A lightweight skill registry for Hermes Agent skills."""
    pass


# Import and register commands
from skillhub.cli.commands.push import push  # noqa: E402
from skillhub.cli.commands.install import install  # noqa: E402
from skillhub.cli.commands.search import search  # noqa: E402
from skillhub.cli.commands.list_cmd import list_skills  # noqa: E402
from skillhub.cli.commands.auth import auth  # noqa: E402

cli.add_command(push)
cli.add_command(install)
cli.add_command(search)
cli.add_command(list_skills, "list")
cli.add_command(auth)


if __name__ == "__main__":
    cli()
