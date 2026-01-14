"""Message sending and command execution commands."""

import subprocess
import sys
import time
from typing import Annotated, Optional

import psutil
import typer
from sqlmodel import select

from goblin_messenger.database import get_session, init_db
from goblin_messenger.discord_client import send_to_discord
from goblin_messenger.models import CommandExecutionResult, DiscordMessage, Webhook

app = typer.Typer()


@app.command()
def send(
    message: Annotated[
        str, typer.Argument(help="Message to send (max 2000 characters)")
    ],
    webhook_name: Annotated[
        Optional[str], typer.Option("--webhook", "-w", help="Webhook name to use")
    ] = None,
    username: Annotated[
        Optional[str],
        typer.Option("--username", "-u", help="Custom username (max 80 characters)"),
    ] = None,
):
    """Send a message to Discord."""
    init_db()

    try:
        discord_msg = DiscordMessage(content=message, username=username)
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)

    with get_session() as session:
        if webhook_name:
            webhook = session.exec(
                select(Webhook).where(Webhook.name == webhook_name)
            ).first()
            if not webhook:
                typer.echo(f"Error: Webhook '{webhook_name}' not found", err=True)
                raise typer.Exit(1)
        else:
            webhook = session.exec(select(Webhook).where(Webhook.is_default)).first()
            if not webhook:
                typer.echo(
                    "Error: No default webhook set. Use --webhook or set a default with save --set-default",
                    err=True,
                )
                raise typer.Exit(1)

        if send_to_discord(webhook.url, discord_msg):
            typer.echo(f"✓ Message sent via '{webhook.name}'")
        else:
            raise typer.Exit(1)


@app.command()
def run(
    command: Annotated[
        list[str], typer.Argument(help="Command to execute and monitor")
    ],
    webhook_name: Annotated[
        Optional[str], typer.Option("--webhook", "-w", help="Webhook name to use")
    ] = None,
    notify_start: Annotated[
        bool,
        typer.Option("--notify-start", help="Send notification when command starts"),
    ] = False,
    include_output: Annotated[
        bool,
        typer.Option("--output", "-o", help="Include stdout/stderr in notification"),
    ] = False,
    no_stream: Annotated[
        bool,
        typer.Option(
            "--no-stream", "-ns",, help="Do not stream output to terminal; capture instead"
        ),
    ] = False,
):
    """Execute a command and send completion notification to Discord."""
    init_db()

    with get_session() as session:
        if webhook_name:
            webhook = session.exec(
                select(Webhook).where(Webhook.name == webhook_name)
            ).first()
            if not webhook:
                typer.echo(f"Error: Webhook '{webhook_name}' not found", err=True)
                raise typer.Exit(1)
        else:
            webhook = session.exec(select(Webhook).where(Webhook.is_default)).first()
            if not webhook:
                typer.echo(
                    "Error: No default webhook set. Use --webhook or set a default with save --set-default",
                    err=True,
                )
                raise typer.Exit(1)

        webhook_url = webhook.url
        webhook_name_str = webhook.name

    cmd_str = " ".join(command)

    if notify_start:
        start_msg = DiscordMessage(content=f"🚀 **Command Started**\n`{cmd_str}`")
        send_to_discord(webhook_url, start_msg)

    typer.echo(f"Running: {cmd_str}")

    start_time = time.time()
    if no_stream:
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    else:
        process = subprocess.Popen(
            command,
            stdout=None,
            stderr=None,
            text=True,
        )

    try:
        psutil_process = psutil.Process(process.pid)
        cpu_percent = psutil_process.cpu_percent(interval=0.1)
        memory_mb = psutil_process.memory_info().rss / 1024 / 1024
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        cpu_percent = 0.0
        memory_mb = 0.0

    if no_stream:
        stdout, stderr = process.communicate()
    else:
        process.wait()
        stdout, stderr = "(streamed to terminal)", "(streamed to terminal)"
    duration = time.time() - start_time

    if include_output and no_stream:
        stdout_value = stdout.strip()
    elif not no_stream:
        stdout_value = "Output was streamed to terminal."
    else:
        stdout_value = "No output specified."

    result = CommandExecutionResult(
        command=cmd_str,
        exit_code=process.returncode if include_output else 0,
        stderr=stderr.strip() if include_output and no_stream else "",
        cpu_percent=cpu_percent,
        memory_mb=memory_mb,
        stdout=stdout_value,
        duration=duration,
    )

    discord_msg = DiscordMessage(content=result.format_discord_message())

    if send_to_discord(webhook_url, discord_msg):
        typer.echo(f"✓ Notification sent via '{webhook_name_str}'")

    sys.exit(process.returncode)
