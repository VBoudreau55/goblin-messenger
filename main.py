<<<<<<< HEAD
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Annotated, Optional

import httpx
import psutil
import typer
from pydantic import BaseModel, Field, field_validator
from sqlmodel import Field as SQLField, Session, SQLModel, create_engine, select

app = typer.Typer(help="Discord notification system for command execution")

DB_PATH = Path.home() / ".goblin-messenger" / "webhooks.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)
DATABASE_URL = f"sqlite:///{DB_PATH}"
engine = create_engine(DATABASE_URL, echo=False)


class Webhook(SQLModel, table=True):
    id: Optional[int] = SQLField(default=None, primary_key=True)
    name: str = SQLField(unique=True, index=True)
    url: str
    is_default: bool = SQLField(default=False)
    created_at: str = SQLField(default_factory=lambda: datetime.utcnow().isoformat())


class DiscordMessage(BaseModel):
    content: str = Field(..., max_length=2000)
    username: Optional[str] = Field(None, max_length=80)

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Message content cannot be empty")
        return v


class CommandExecutionResult(BaseModel):
    command: str
    exit_code: int
    duration: float
    cpu_percent: float
    memory_mb: float
    stdout: str = Field(default="", max_length=1500)
    stderr: str = Field(default="", max_length=1500)

    def format_discord_message(self) -> str:
        status_emoji = "✅" if self.exit_code == 0 else "❌"
        status_text = "SUCCESS" if self.exit_code == 0 else "FAILED"

        msg = f"{status_emoji} **Command {status_text}**\n\n"
        msg += f"**Command:** `{self.command}`\n"
        msg += f"**Exit Code:** {self.exit_code}\n"
        msg += f"**Duration:** {self.duration:.2f}s\n"
        msg += f"**CPU:** {self.cpu_percent:.1f}%\n"
        msg += f"**Memory:** {self.memory_mb:.1f}MB\n"

        if self.stdout:
            truncated_stdout = self.stdout[:500]
            if len(self.stdout) > 500:
                truncated_stdout += "\n... (truncated)"
            msg += f"\n**Output:**\n```\n{truncated_stdout}\n```"

        if self.stderr:
            truncated_stderr = self.stderr[:500]
            if len(self.stderr) > 500:
                truncated_stderr += "\n... (truncated)"
            msg += f"\n**Errors:**\n```\n{truncated_stderr}\n```"

        if len(msg) > 2000:
            msg = msg[:1997] + "..."

        return msg


def init_db():
    SQLModel.metadata.create_all(engine)


def get_session():
    return Session(engine)


def send_to_discord(webhook_url: str, message: DiscordMessage) -> bool:
    try:
        with httpx.Client(timeout=10.0) as client:
            payload = {"content": message.content}
            if message.username:
                payload["username"] = message.username

            response = client.post(webhook_url, json=payload)
            response.raise_for_status()
            return True
    except Exception as e:
        typer.echo(f"Error sending to Discord: {e}", err=True)
        return False


@app.command()
def save(
    name: Annotated[str, typer.Argument(help="Name for this webhook")],
    url: Annotated[str, typer.Argument(help="Discord webhook URL")],
    set_default: Annotated[
        bool, typer.Option("--set-default", "-d", help="Set as default webhook")
    ] = False,
):
    """Save a Discord webhook URL"""
    init_db()

    with get_session() as session:
        existing = session.exec(select(Webhook).where(Webhook.name == name)).first()
        if existing:
            typer.echo(f"Error: Webhook '{name}' already exists", err=True)
            raise typer.Exit(1)

        if set_default:
            for webhook in session.exec(
                select(Webhook).where(Webhook.is_default == True)
            ):
                webhook.is_default = False
                session.add(webhook)

        webhook = Webhook(name=name, url=url, is_default=set_default)
        session.add(webhook)
        session.commit()

        default_msg = " (set as default)" if set_default else ""
        typer.echo(f"✓ Saved webhook '{name}'{default_msg}")


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
    """Send a message to Discord"""
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
            webhook = session.exec(
                select(Webhook).where(Webhook.is_default == True)
            ).first()
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
):
    """Execute a command and send completion notification to Discord"""
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
            webhook = session.exec(
                select(Webhook).where(Webhook.is_default == True)
            ).first()
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
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    try:
        psutil_process = psutil.Process(process.pid)
        cpu_percent = psutil_process.cpu_percent(interval=0.1)
        memory_mb = psutil_process.memory_info().rss / 1024 / 1024
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        cpu_percent = 0.0
        memory_mb = 0.0

    stdout, stderr = process.communicate()
    duration = time.time() - start_time

    result = CommandExecutionResult(
        command=cmd_str,
        exit_code=process.returncode,
        duration=duration,
        cpu_percent=cpu_percent,
        memory_mb=memory_mb,
        stdout=stdout.strip(),
        stderr=stderr.strip(),
    )

    discord_msg = DiscordMessage(content=result.format_discord_message())

    if send_to_discord(webhook_url, discord_msg):
        typer.echo(f"✓ Notification sent via '{webhook_name_str}'")

    sys.exit(process.returncode)


@app.command()
def list():
    """List all saved webhooks"""
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
    """Delete a saved webhook"""
    init_db()

    with get_session() as session:
        webhook = session.exec(select(Webhook).where(Webhook.name == name)).first()

        if not webhook:
            typer.echo(f"Error: Webhook '{name}' not found", err=True)
            raise typer.Exit(1)

        session.delete(webhook)
        session.commit()
        typer.echo(f"✓ Deleted webhook '{name}'")


def main():
    app()
=======
def main():
    print("Hello from goblin-messenger!")
>>>>>>> main


if __name__ == "__main__":
    main()
