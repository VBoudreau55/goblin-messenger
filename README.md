# goblin-messenger

> **Note**: This was a quick ai-assisted CLI app to send Discord notifications to my phone when I kick off long-running processes on my computer. The reasoning behind the name is to match the theme of my discord profile which is a goblin and themed around goblins (mostly from magic the gathering).

A Discord notification system for command execution monitoring. Get notified on Discord (and your phone via the Discord mobile app) when your commands complete, with detailed execution metrics.

## Installation

### Using uv (recommended)

```bash
# Clone the repo
git clone https://github.com/VBoudreau55/goblin-messenger.git
cd goblin-messenger

# Install with uv
uv sync

# Use the CLI
uv run goblinmsg --help
# Or use the short alias
uv run gmsg --help
```

### Using pip

```bash
# Clone the repo
git clone https://github.com/VBoudreau55/goblin-messenger.git
cd goblin-messenger

# Install the package
pip install -e .

# Use the CLI (both commands work)
goblinmsg --help
gmsg --help
```

## Quick Start

### 1. Get a Discord Webhook URL

1. Open Discord and go to a server where you have admin permissions
2. Right-click a channel → Edit Channel → Integrations → Webhooks
3. Create a new webhook and copy the URL
4. Install Discord mobile app and enable notifications for that channel

### 2. Save Your Webhook

```bash
goblinmsg save my-phone https://discord.com/api/webhooks/YOUR_WEBHOOK_URL --set-default
# Or use the short alias
gmsg save my-phone https://discord.com/api/webhooks/YOUR_WEBHOOK_URL --set-default
```

### 3. Run a Command with Notifications

```bash
# Get notified when it completes
goblinmsg run npm run build

# Get notified at start AND completion
goblinmsg run --notify-start python train_model.py

# Include command output in the notification
gmsg run --output pytest tests/
```

### 4. Send Quick Messages

```bash
gmsg send "Build finished! 🎉"
```

## Commands Reference

### `save`

Save a Discord webhook URL.

```bash
goblinmsg save <name> <url> [--set-default]
```

### `send`

Send a message to Discord.

```bash
gmsg send <message> [--webhook NAME] [--username USERNAME]
```

### `run`

Execute a command and send completion notification.

```bash
goblinmsg run [OPTIONS] <command>
```

Options:

- `--webhook, -w`: Specify webhook to use (uses default if not specified)
- `--notify-start`: Send notification when command starts
- `--output, -o`: Include stdout/stderr in notification (off by default)

### `set-default`

Set a saved webhook as the default.

```bash
goblinmsg set-default <name>
```

### `list`

List all saved webhooks (shows which is default).

```bash
goblinmsg list
```

### `delete`

Delete a saved webhook.

```bash
goblinmsg delete <name>
```

## Examples

### Monitor a long-running build

```bash
goblinmsg run --notify-start npm run build
```

### Send custom alert with custom username

```bash
gmsg send "🚨 Production deployment complete" --username "Deploy Bot"
```

### Run with output included

```bash
goblinmsg run --output python script.py
```

### Multiple webhooks

```bash
# Save webhooks for different channels
goblinmsg save personal https://discord.com/api/webhooks/... --set-default
goblinmsg save work https://discord.com/api/webhooks/...

# Use specific webhook
gmsg send "Personal reminder" --webhook personal

# Change default
goblinmsg set-default work
```

## Platform Notes

### Windows

Use PowerShell commands for testing:

```bash3
goblinmsg run timeout /t 5
gmsg run powershell -Command "Start-Sleep -Seconds 10"
```

### Linux/macOS

```bash
goblinmsg run sleep 5
gmsg run ./long-script.sh
```

## What Gets Sent

The notification includes:

- ✅/❌ Success/failure status emoji
- Command executed
- Exit code
- Duration in seconds
- CPU usage percentage
- Memory usage in MB
- stdout/stderr (only if `--output` flag is used, truncated to 500 chars each)

## Technical Details

**Built with:**

- **Typer**: CLI framework
- **SQLModel**: ORM for webhook storage
- **SQLite**: Local database (~/.goblin-messenger/webhooks.db)
- **psutil**: Process monitoring
- **httpx**: Discord API client
- **Pydantic**: Input validation

**AI Disclaimer**: This project was built with significant AI assistance for rapid prototyping and learning.

## License

See [LICENSE](LICENSE) file.