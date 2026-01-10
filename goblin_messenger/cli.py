"""Main CLI application entry point."""

import typer

from goblin_messenger import message_commands, webhook_commands

app = typer.Typer(help="Discord notification system for command execution")

# Add webhook management commands
app.add_typer(webhook_commands.app, name="webhook", help="Manage Discord webhooks")

# Add message commands at the root level for convenience
app.command(name="send")(message_commands.send)
app.command(name="run")(message_commands.run)

# Add webhook commands at root level for backward compatibility
app.command(name="save")(webhook_commands.save)
app.command(name="list")(webhook_commands.list)
app.command(name="delete")(webhook_commands.delete)
app.command(name="set-default")(webhook_commands.set_default)


def main():
    """Entry point for the CLI application."""
    app()


if __name__ == "__main__":
    main()
