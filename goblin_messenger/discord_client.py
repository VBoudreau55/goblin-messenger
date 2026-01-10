"""Discord HTTP client for sending messages to webhooks."""

import httpx
import typer

from goblin_messenger.models import DiscordMessage


def send_to_discord(webhook_url: str, message: DiscordMessage) -> bool:
    """
    Send a message to Discord via webhook.

    Args:
        webhook_url: The Discord webhook URL to send the message to
        message: The message to send

    Returns:
        True if the message was sent successfully, False otherwise
    """
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
