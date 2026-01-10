"""Webhook management commands."""

from typing import Annotated

import typer
from sqlmodel import select

from goblin_messenger.database import get_session, init_db
from goblin_messenger.models import Webhook

app = typer.Typer()


@app.command()
def save(
    name: Annotated[str, typer.Argument(help="Name for this webhook")],
    url: Annotated[str, typer.Argument(help="Discord webhook URL")],
    set_default: Annotated[
        bool, typer.Option("--set-default", "-d", help="Set as default webhook")
    ] = False,
):
    """Save a Discord webhook URL."""
    init_db()

    with get_session() as session:
        existing = session.exec(select(Webhook).where(Webhook.name == name)).first()
        if existing:
            typer.echo(f"Error: Webhook '{name}' already exists", err=True)
            raise typer.Exit(1)

        if set_default:
            for webhook in session.exec(select(Webhook).where(Webhook.is_default)):
                webhook.is_default = False
                session.add(webhook)

        webhook = Webhook(name=name, url=url, is_default=set_default)
        session.add(webhook)
        session.commit()

        default_msg = " (set as default)" if set_default else ""
        typer.echo(f"✓ Saved webhook '{name}'{default_msg}")


@app.command()
def list():
    """List all saved webhooks."""
    init_db()

    with get_session() as session:
        webhooks = session.exec(select(Webhook)).all()

        if not webhooks:
            typer.echo("No webhooks saved")
            return

        typer.echo("\nSaved webhooks:")
        for webhook in webhooks:
            default_marker = " [DEFAULT]" if webhook.is_default else ""
            typer.echo(f"  • {webhook.name}{default_marker}")
            typer.echo(f"    URL: {webhook.url[:50]}...")
            typer.echo(f"    Created: {webhook.created_at}")
            typer.echo()


@app.command()
def delete(
    name: Annotated[str, typer.Argument(help="Name of webhook to delete")],
):
    """Delete a saved webhook."""
    init_db()

    with get_session() as session:
        webhook = session.exec(select(Webhook).where(Webhook.name == name)).first()

        if not webhook:
            typer.echo(f"Error: Webhook '{name}' not found", err=True)
            raise typer.Exit(1)

        session.delete(webhook)
        session.commit()
        typer.echo(f"✓ Deleted webhook '{name}'")


@app.command(name="set-default")
def set_default(
    name: Annotated[str, typer.Argument(help="Name of webhook to set as default")],
):
    """Set a webhook as the default."""
    init_db()

    with get_session() as session:
        webhook = session.exec(select(Webhook).where(Webhook.name == name)).first()

        if not webhook:
            typer.echo(f"Error: Webhook '{name}' not found", err=True)
            raise typer.Exit(1)

        # Clear any existing default
        for existing_default in session.exec(select(Webhook).where(Webhook.is_default)):
            existing_default.is_default = False
            session.add(existing_default)

        # Set this webhook as default
        webhook.is_default = True
        session.add(webhook)
        session.commit()

        typer.echo(f"✓ Set '{name}' as default webhook")
