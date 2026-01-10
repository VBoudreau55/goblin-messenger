# goblin-messenger

A Discord notification system for command execution monitoring. Get notified on Discord when your commands complete, with detailed execution metrics.

## Features

- 💾 **Webhook Management**: Save and manage multiple Discord webhooks
- 📨 **Direct Messaging**: Send messages directly to Discord
- 🔄 **Command Monitoring**: Execute commands and get notified on completion
- 📊 **Execution Metrics**: Track CPU usage, memory, duration, and exit codes
- ✅ **Pydantic Validation**: All inputs validated with character limits (2000 for messages, 80 for usernames)
- 🎯 **Default Webhook**: Set a default webhook for quick notifications

## Installation

```bash
uv sync
```

## Quick Start

### 1. Save a Discord Webhook

```bash
python main.py save my-webhook https://discord.com/api/webhooks/... --set-default
```

### 2. Send a Message

```bash
python main.py send "Hello from goblin-messenger!"
```

With custom username:
```bash
python main.py send "Build completed" --username "CI/CD Bot"
```

### 3. Monitor a Command

```bash
python main.py run pytest tests/
```

With start notification:
```bash
python main.py run --notify-start npm run build
```

## Commands

### `save`
Save a Discord webhook URL.

```bash
python main.py save <name> <url> [--set-default]
```

Options:
- `--set-default, -d`: Set this webhook as the default

### `send`
Send a message to Discord.

```bash
python main.py send <message> [--webhook NAME] [--username USERNAME]
```

Options:
- `--webhook, -w`: Specify webhook to use (uses default if not specified)
- `--username, -u`: Custom username for the message (max 80 characters)

Validation:
- Message content: max 2000 characters
- Username: max 80 characters
- Content cannot be empty

### `run`
Execute a command and send completion notification.

```bash
python main.py run [--webhook NAME] [--notify-start] -- <command>
```

Options:
- `--webhook, -w`: Specify webhook to use (uses default if not specified)
- `--notify-start`: Send notification when command starts

The notification includes:
- ✅/❌ Success/failure status
- Command executed
- Exit code
- Duration
- CPU usage (%)
- Memory usage (MB)
- stdout (truncated to 500 chars)
- stderr (truncated to 500 chars)

### `list`
List all saved webhooks.

```bash
python main.py list
```

### `delete`
Delete a saved webhook.

```bash
python main.py delete <name>
```

## Examples

### Monitor a long-running build
```bash
python main.py run --notify-start -- npm run build
```

### Send custom alert
```bash
python main.py send "🚨 Production deployment starting" --username "Deploy Bot"
```

### Multiple webhooks
```bash
# Save webhooks for different channels
python main.py save dev-alerts https://discord.com/api/webhooks/dev... --set-default
python main.py save prod-alerts https://discord.com/api/webhooks/prod...

# Use specific webhook
python main.py send "Prod deployment complete" --webhook prod-alerts
```

## Architecture

- **Typer**: CLI framework with rich help messages
- **Pydantic**: Input validation with character limits
- **SQLModel**: Database ORM for webhook storage
- **SQLite**: Local database (~/.goblin-messenger/webhooks.db)
- **psutil**: Process monitoring for CPU and memory metrics
- **httpx**: HTTP client for Discord API

## Data Models

### Webhook (SQLModel)
- `id`: Primary key
- `name`: Unique webhook name
- `url`: Discord webhook URL
- `is_default`: Default webhook flag
- `created_at`: Creation timestamp

### DiscordMessage (Pydantic)
- `content`: Message content (max 2000 chars)
- `username`: Optional custom username (max 80 chars)

### CommandExecutionResult (Pydantic)
- `command`: Command string
- `exit_code`: Process exit code
- `duration`: Execution time in seconds
- `cpu_percent`: CPU usage percentage
- `memory_mb`: Memory usage in MB
- `stdout`: Standard output (truncated)
- `stderr`: Standard error (truncated)