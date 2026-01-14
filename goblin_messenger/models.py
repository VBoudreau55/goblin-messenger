"""Data models for Goblin Messenger."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator
from sqlmodel import Field as SQLField, SQLModel


class Webhook(SQLModel, table=True):
    """Database model for storing Discord webhooks."""

    id: Optional[int] = SQLField(default=None, primary_key=True)
    name: str = SQLField(unique=True, index=True)
    url: str
    is_default: bool = SQLField(default=False)
    created_at: str = SQLField(default_factory=lambda: datetime.utcnow().isoformat())


class DiscordMessage(BaseModel):
    """Model for validating Discord message payloads."""

    content: str = Field(..., max_length=2000)
    username: Optional[str] = Field(None, max_length=80)

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Message content cannot be empty")
        return v


class CommandExecutionResult(BaseModel):
    """Model for storing and formatting command execution results."""

    command: str
    exit_code: int
    duration: float
    cpu_percent: float
    memory_mb: float
    stdout: str = Field(default="", max_length=1500)
    stderr: str = Field(default="", max_length=1500)

    def format_discord_message(self) -> str:
        """Format the execution result as a Discord message."""
        status_emoji = "✅" if self.exit_code == 0 else "❌"
        status_text = "SUCCESS" if self.exit_code == 0 else "FAILED"

        msg = f"{status_emoji} **Command {status_text}**\n\n"
        msg += f"**Command:** `{self.command}`\n"
        msg += f"**Exit Code:** {self.exit_code}\n"
        msg += f"**Duration:** {self.duration:.2f}s\n"
        msg += f"**CPU:** {self.cpu_percent:.1f}%\n"
        msg += f"**Memory:** {self.memory_mb:.1f}MB\n"

        if self.stdout:
            truncated_stdout = self.stdout[:100]
            if len(self.stdout) > 100:
                truncated_stdout += "\n... (truncated)"
            msg += f"\n**Output:**\n```\n{truncated_stdout}\n```"

        if self.stderr:
            truncated_stderr = self.stderr[:100]
            if len(self.stderr) > 100:
                truncated_stderr += "\n... (truncated)"
            msg += f"\n**Errors:**\n```\n{truncated_stderr}\n```"

        if len(msg) > 1000:
            msg = msg[:997] + "..."

        return msg
