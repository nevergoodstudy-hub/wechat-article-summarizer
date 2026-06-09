"""CLI展示层"""

from .app import cli


def run_cli() -> None:
    """Run the CLI through the application composition root."""
    from ...bootstrap.cli import run_cli as run_bootstrapped_cli

    run_bootstrapped_cli()


__all__ = ["cli", "run_cli"]
