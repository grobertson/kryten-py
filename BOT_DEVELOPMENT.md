# Kryten-py Bot Development Guide

A comprehensive guide for building CyTube bots using the kryten-py library.

## Table of Contents

- [Getting Started](#getting-started)
- [Bot Architecture](#bot-architecture)
- [Configuration](#configuration)
- [Event Handling](#event-handling)
- [Sending Commands](#sending-commands)
- [Common Patterns](#common-patterns)
- [Example Bots](#example-bots)
- [Testing Your Bot](#testing-your-bot)
- [Deployment](#deployment)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

## Getting Started

### Prerequisites

- **Python 3.11 or higher**
- **Poetry** (recommended) or pip
- **NATS server** running (or access to one)
- **Kryten Bridge** connected to your CyTube server

### Installation

**Using Poetry** (Recommended):
```bash
poetry add kryten-py
```

**Using pip**:
```bash
pip install kryten-py
```

### Your First Bot

Create a file `my_bot.py`:

```python
import asyncio
import logging
from kryten import KrytenClient, ChatMessageEvent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

async def main():
    """Simple echo bot."""
    
    # Configuration
    config = {
        "nats": {
            "servers": ["nats://localhost:4222"]
        },
        "channels": [
            {"domain": "cytu.be", "channel": "lounge"}
        ]
    }
    
    # Create client
    async with KrytenClient(config) as client:
        
        @client.on("chatmsg")
        async def on_chat(event: ChatMessageEvent):
            """Echo user messages."""
            if event.username != "MyBot":  # Don't echo ourselves
                await client.send_chat(
                    event.channel,
                    f"Echo: {event.message}"
                )
        
        print("Bot started! Press Ctrl+C to stop.")
        await client.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nBot stopped by user")
```

Run your bot:
```bash
python my_bot.py
```

## Bot Architecture

### Basic Structure

```python
async def main():
    # 1. Configure client
    config = {...}
    
    # 2. Create client (use context manager)
    async with KrytenClient(config) as client:
        
        # 3. Register event handlers
        @client.on("chatmsg")
        async def handler(event):
            # Handle event
            pass
        
        # 4. Run event loop
        await client.run()

# 5. Entry point
if __name__ == "__main__":
    asyncio.run(main())
```

### Component Breakdown

**1. Configuration**
- NATS connection settings
- Channel subscriptions
- Retry/timeout settings

**2. Event Handlers**
- Registered with `@client.on()` decorator
- Async functions that receive event objects
- Multiple handlers can listen to same event

**3. Commands**
- Methods to send actions to CyTube
- Chat, playlist, playback, moderation
- Async methods that return immediately

**4. Event Loop**
- `client.run()` starts the bot
- Blocks until stopped (Ctrl+C)
- Handles reconnection automatically

### Lifecycle

```
┌─────────────┐
│   Create    │
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Connect    │
│  to NATS    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Subscribe   │
│ to Events   │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Run       │
│   Loop      │◄──┐
└──────┬──────┘   │
       │          │
       ▼          │
┌─────────────┐   │
│  Receive    │   │
│   Event     │   │
└──────┬──────┘   │
       │          │
       ▼          │
┌─────────────┐   │
│  Dispatch   │   │
│  Handlers   │   │
└──────┬──────┘   │
       │          │
       └──────────┘
```

## Configuration

### Basic Configuration

**Dictionary-based** (simple):
```python
config = {
    "nats": {
        "servers": ["nats://localhost:4222"]
    },
    "channels": [
        {"domain": "cytu.be", "channel": "lounge"}
    ]
}
```

### From JSON File

**config.json**:
```json
{
  "nats": {
    "servers": ["nats://localhost:4222"],
    "user": "${NATS_USER}",
    "password": "${NATS_PASSWORD}"
  },
  "channels": [
    {"domain": "cytu.be", "channel": "lounge"},
    {"domain": "cytu.be", "channel": "anime"}
  ],
  "retry_attempts": 3,
  "handler_timeout": 30.0
}
```

**Load in bot**:
```python
from kryten import KrytenConfig

config = KrytenConfig.from_json("config.json")
async with KrytenClient(config) as client:
    ...
```

### Environment Variables

Use `${VAR_NAME}` in JSON for environment variable substitution:

```json
{
  "nats": {
    "servers": ["${NATS_SERVER}"],
    "user": "${NATS_USER}",
    "password": "${NATS_PASSWORD}"
  }
}
```

Set environment variables:
```bash
# Linux/Mac
export NATS_SERVER=nats://prod.example.com:4222
export NATS_USER=bot_user
export NATS_PASSWORD=secret

# Windows PowerShell
$env:NATS_SERVER="nats://prod.example.com:4222"
$env:NATS_USER="bot_user"
$env:NATS_PASSWORD="secret"
```

### Advanced Configuration

**With TLS**:
```python
config = {
    "nats": {
        "servers": ["nats://localhost:4222"],
        "tls": True,
        "tls_ca_cert": "/path/to/ca.pem"
    },
    "channels": [...]
}
```

**Multiple Channels**:
```python
config = {
    "nats": {...},
    "channels": [
        {"domain": "cytu.be", "channel": "lounge"},
        {"domain": "cytu.be", "channel": "anime"},
        {"domain": "localhost", "channel": "test"}
    ]
}
```

**Tuning**:
```python
config = {
    "nats": {...},
    "channels": [...],
    "retry_attempts": 5,          # Retry failed publishes 5 times
    "retry_delay": 0.2,           # 200ms initial delay
    "handler_timeout": 60.0,      # Handler timeout: 60 seconds
    "reconnect_delay": 2.0        # Reconnect delay: 2 seconds
}
```

## Event Handling

### Available Events

| Event Name | Event Type | Description |
|------------|-----------|-------------|
| `chatmsg` | `ChatMessageEvent` | User sent chat message |
| `addUser` | `UserJoinEvent` | User joined channel |
| `userLeave` | `UserLeaveEvent` | User left channel |
| `changeMedia` | `ChangeMediaEvent` | Video changed |
| `playlist` | `PlaylistUpdateEvent` | Playlist modified |

### Event Handler Basics

**Simple Handler**:
```python
@client.on("chatmsg")
async def on_chat(event: ChatMessageEvent):
    print(f"{event.username}: {event.message}")
```

**Channel-Specific**:
```python
@client.on("chatmsg", channel="lounge")
async def on_lounge_chat(event: ChatMessageEvent):
    # Only messages from #lounge
    print(f"[Lounge] {event.username}: {event.message}")
```

**Domain-Specific**:
```python
@client.on("chatmsg", domain="cytu.be")
async def on_cytube_chat(event: ChatMessageEvent):
    # Only messages from cytu.be channels
    print(f"[CyTube] {event.username}: {event.message}")
```

**Multiple Handlers**:
```python
# Both will be called for each chat message
@client.on("chatmsg")
async def log_chat(event: ChatMessageEvent):
    logger.info(f"{event.username}: {event.message}")

@client.on("chatmsg")
async def respond_to_chat(event: ChatMessageEvent):
    if "!help" in event.message:
        await client.send_chat(event.channel, "Available commands: !help, !roll")
```

### Event Types

**ChatMessageEvent**:
```python
@client.on("chatmsg")
async def on_chat(event: ChatMessageEvent):
    print(f"Channel: {event.channel}")
    print(f"Domain: {event.domain}")
    print(f"Username: {event.username}")
    print(f"Message: {event.message}")
    print(f"Time: {event.time}")
    print(f"Timestamp: {event.timestamp}")
```

**UserJoinEvent**:
```python
@client.on("addUser")
async def on_user_join(event: UserJoinEvent):
    await client.send_chat(
        event.channel,
        f"Welcome, {event.name}!"
    )
```

**UserLeaveEvent**:
```python
@client.on("userLeave")
async def on_user_leave(event: UserLeaveEvent):
    print(f"{event.name} left the channel")
```

**ChangeMediaEvent**:
```python
@client.on("changeMedia")
async def on_media_change(event: ChangeMediaEvent):
    print(f"Now playing: {event.title}")
    print(f"Duration: {event.seconds}s")
    print(f"Type: {event.type}")  # yt, vm, etc.
    print(f"ID: {event.id}")
```

**PlaylistUpdateEvent**:
```python
@client.on("playlist")
async def on_playlist_update(event: PlaylistUpdateEvent):
    print(f"Playlist action: {event.action}")  # add, delete, move, etc.
    if event.item:
        print(f"Item: {event.item.title}")
```

### Error Handling in Handlers

**Try-Except Pattern**:
```python
@client.on("chatmsg")
async def on_chat(event: ChatMessageEvent):
    try:
        # Your logic here
        result = await process_message(event.message)
        await client.send_chat(event.channel, result)
    except ValueError as e:
        # Handle specific errors
        await client.send_chat(event.channel, f"Error: {e}")
    except Exception as e:
        # Catch-all for unexpected errors
        logger.error(f"Handler error: {e}", exc_info=True)
```

**Timeouts**:
```python
import asyncio

@client.on("chatmsg")
async def on_chat(event: ChatMessageEvent):
    try:
        # Long-running operation
        result = await asyncio.wait_for(
            slow_operation(event.message),
            timeout=5.0
        )
        await client.send_chat(event.channel, result)
    except asyncio.TimeoutError:
        await client.send_chat(event.channel, "Operation timed out")
```

## Sending Commands

### Chat Commands

**Send Chat Message**:
```python
await client.send_chat(
    channel="lounge",
    message="Hello, everyone!",
    metadata={"bot_version": "1.0"}  # Optional
)
```

**Send Private Message**:
```python
await client.send_pm(
    channel="lounge",
    username="Alice",
    message="Hello, Alice!",
    metadata={}  # Optional
)
```

### Playlist Commands

**Add Media**:
```python
await client.add_media(
    channel="lounge",
    media_type="yt",  # YouTube
    url="https://youtube.com/watch?v=dQw4w9WgXcQ",
    title="Rick Astley - Never Gonna Give You Up",  # Optional
    duration=213,  # Optional, seconds
    temp=False  # Optional, temporary video
)
```

**Delete Media**:
```python
await client.delete_media(
    channel="lounge",
    uid="abc123"  # Video UID from playlist
)
```

**Move Media**:
```python
await client.move_media(
    channel="lounge",
    from_position=5,
    to_position=1  # Move to top of queue
)
```

**Jump to Video**:
```python
await client.jump_to(
    channel="lounge",
    uid="abc123"  # Video UID
)
```

**Clear Playlist**:
```python
await client.clear_playlist(channel="lounge")
```

**Shuffle Playlist**:
```python
await client.shuffle_playlist(channel="lounge")
```

**Set Temporary**:
```python
await client.set_temp(
    channel="lounge",
    uid="abc123",
    is_temp=True  # Mark as temporary
)
```

### Playback Commands

**Pause**:
```python
await client.pause(channel="lounge")
```

**Play**:
```python
await client.play(channel="lounge")
```

**Seek**:
```python
await client.seek(
    channel="lounge",
    time_seconds=30.5  # Seek to 30.5 seconds
)
```

### Moderation Commands

**Kick User**:
```python
await client.kick_user(
    channel="lounge",
    username="Spammer123",
    reason="Spam"  # Optional
)
```

**Ban User**:
```python
await client.ban_user(
    channel="lounge",
    username="BadUser",
    reason="Violation of rules"  # Optional
)
```

**Vote Skip**:
```python
await client.voteskip(channel="lounge")
```

## Common Patterns

### Command Bot

Respond to `!commands` in chat:

```python
@client.on("chatmsg")
async def command_handler(event: ChatMessageEvent):
    """Handle bot commands."""
    
    # Ignore our own messages
    if event.username == "MyBot":
        return
    
    message = event.message.strip()
    
    # !help command
    if message == "!help":
        await client.send_chat(
            event.channel,
            "Commands: !help, !roll, !time, !skip"
        )
    
    # !roll command (dice roll)
    elif message == "!roll":
        import random
        roll = random.randint(1, 6)
        await client.send_chat(
            event.channel,
            f"{event.username} rolled a {roll}!"
        )
    
    # !time command
    elif message == "!time":
        from datetime import datetime
        now = datetime.now().strftime("%H:%M:%S")
        await client.send_chat(
            event.channel,
            f"Current time: {now}"
        )
    
    # !skip command (vote skip)
    elif message == "!skip":
        await client.voteskip(event.channel)
        await client.send_chat(
            event.channel,
            f"{event.username} voted to skip"
        )
```

### DJ Bot

Auto-add videos from queue:

```python
import asyncio
from collections import deque

class DJBot:
    def __init__(self, client, channel):
        self.client = client
        self.channel = channel
        self.queue = deque()
        self.is_playing = False
    
    async def add_to_queue(self, video_url, username):
        """Add video to queue."""
        self.queue.append((video_url, username))
        await self.client.send_chat(
            self.channel,
            f"Added to queue (position {len(self.queue)})"
        )
        
        # Start playing if not already
        if not self.is_playing:
            await self.play_next()
    
    async def play_next(self):
        """Play next video from queue."""
        if not self.queue:
            self.is_playing = False
            return
        
        self.is_playing = True
        video_url, username = self.queue.popleft()
        
        await self.client.add_media(
            self.channel,
            media_type="yt",
            url=video_url,
            temp=True  # Auto-remove after playing
        )
        
        await self.client.send_chat(
            self.channel,
            f"Now playing: requested by {username}"
        )

# Usage
dj = DJBot(client, "lounge")

@client.on("chatmsg")
async def on_chat(event: ChatMessageEvent):
    if event.message.startswith("!add "):
        url = event.message[5:].strip()
        if "youtube.com" in url or "youtu.be" in url:
            await dj.add_to_queue(url, event.username)

@client.on("changeMedia")
async def on_media_change(event: ChangeMediaEvent):
    # Auto-play next when current video ends
    await asyncio.sleep(event.seconds + 1)
    await dj.play_next()
```

### Greeter Bot

Welcome new users:

```python
@client.on("addUser")
async def greet_user(event: UserJoinEvent):
    """Greet new users."""
    await client.send_chat(
        event.channel,
        f"Welcome to the channel, {event.name}! 👋"
    )

@client.on("userLeave")
async def farewell_user(event: UserLeaveEvent):
    """Say goodbye to leaving users."""
    await client.send_chat(
        event.channel,
        f"Goodbye, {event.name}! Come back soon!"
    )
```

### Moderator Bot

Auto-moderate chat:

```python
import re

BANNED_WORDS = ["spam", "badword1", "badword2"]
WARNING_COUNT = {}

@client.on("chatmsg")
async def moderate_chat(event: ChatMessageEvent):
    """Auto-moderate chat messages."""
    
    message_lower = event.message.lower()
    
    # Check for banned words
    for word in BANNED_WORDS:
        if word in message_lower:
            # Warn user
            warnings = WARNING_COUNT.get(event.username, 0) + 1
            WARNING_COUNT[event.username] = warnings
            
            await client.send_pm(
                event.channel,
                event.username,
                f"Warning {warnings}/3: Please avoid inappropriate language"
            )
            
            # Ban after 3 warnings
            if warnings >= 3:
                await client.ban_user(
                    event.channel,
                    event.username,
                    reason="Repeated violations"
                )
                await client.send_chat(
                    event.channel,
                    f"{event.username} has been banned for repeated violations"
                )
            return
    
    # Check for spam (repeated messages)
    # (Implementation left as exercise)
```

### Statistics Bot

Track channel statistics:

```python
from datetime import datetime
from collections import defaultdict

class Stats:
    def __init__(self):
        self.message_count = defaultdict(int)
        self.total_messages = 0
        self.start_time = datetime.now()
    
    def record_message(self, username):
        self.message_count[username] += 1
        self.total_messages += 1
    
    def get_stats(self):
        uptime = datetime.now() - self.start_time
        top_users = sorted(
            self.message_count.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        return {
            "uptime": str(uptime).split('.')[0],
            "total_messages": self.total_messages,
            "top_users": top_users
        }

stats = Stats()

@client.on("chatmsg")
async def track_message(event: ChatMessageEvent):
    stats.record_message(event.username)

@client.on("chatmsg")
async def stats_command(event: ChatMessageEvent):
    if event.message == "!stats":
        s = stats.get_stats()
        await client.send_chat(
            event.channel,
            f"Uptime: {s['uptime']} | Messages: {s['total_messages']}"
        )
```

### Scheduled Tasks

Run periodic tasks:

```python
import asyncio
from datetime import datetime

async def scheduled_announcements(client, channel):
    """Send periodic announcements."""
    while True:
        await asyncio.sleep(3600)  # Every hour
        
        now = datetime.now()
        await client.send_chat(
            channel,
            f"Hourly reminder: Be kind and have fun! (Time: {now.strftime('%H:%M')})"
        )

# Start in background
async def main():
    async with KrytenClient(config) as client:
        # Register handlers
        @client.on("chatmsg")
        async def handler(event):
            pass
        
        # Start scheduled task
        asyncio.create_task(scheduled_announcements(client, "lounge"))
        
        # Run bot
        await client.run()
```

## Example Bots

### Complete Echo Bot

```python
"""
Echo Bot - Repeats user messages
"""
import asyncio
import logging
from kryten import KrytenClient, ChatMessageEvent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    config = {
        "nats": {"servers": ["nats://localhost:4222"]},
        "channels": [{"domain": "cytu.be", "channel": "lounge"}]
    }
    
    async with KrytenClient(config) as client:
        
        @client.on("chatmsg")
        async def on_chat(event: ChatMessageEvent):
            if event.username != "EchoBot":
                await client.send_chat(
                    event.channel,
                    f"{event.username} said: {event.message}"
                )
        
        logger.info("Echo bot started!")
        await client.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
```

### Complete Roll Bot

```python
"""
Roll Bot - Dice rolling bot
"""
import asyncio
import logging
import random
import re
from kryten import KrytenClient, ChatMessageEvent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    config = {
        "nats": {"servers": ["nats://localhost:4222"]},
        "channels": [{"domain": "cytu.be", "channel": "lounge"}]
    }
    
    async with KrytenClient(config) as client:
        
        @client.on("chatmsg")
        async def on_chat(event: ChatMessageEvent):
            message = event.message.strip()
            
            # !help
            if message == "!help":
                await client.send_chat(
                    event.channel,
                    "Commands: !roll [NdN] - Roll dice (e.g., !roll 2d6)"
                )
            
            # !roll or !roll NdN
            elif message.startswith("!roll"):
                parts = message.split()
                
                if len(parts) == 1:
                    # Simple 1d6
                    result = random.randint(1, 6)
                    await client.send_chat(
                        event.channel,
                        f"{event.username} rolled {result}"
                    )
                else:
                    # Parse NdN format
                    match = re.match(r"(\d+)d(\d+)", parts[1])
                    if match:
                        num_dice = int(match.group(1))
                        num_sides = int(match.group(2))
                        
                        if num_dice > 10 or num_sides > 100:
                            await client.send_chat(
                                event.channel,
                                "Too many dice or sides! Max: 10d100"
                            )
                            return
                        
                        rolls = [random.randint(1, num_sides) for _ in range(num_dice)]
                        total = sum(rolls)
                        
                        await client.send_chat(
                            event.channel,
                            f"{event.username} rolled {num_dice}d{num_sides}: "
                            f"{rolls} = {total}"
                        )
        
        logger.info("Roll bot started!")
        await client.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
```

## Testing Your Bot

### Using MockKrytenClient

Test without NATS server:

```python
import pytest
from kryten import MockKrytenClient, ChatMessageEvent

@pytest.mark.asyncio
async def test_echo_bot():
    """Test echo bot responds correctly."""
    
    config = {
        "nats": {"servers": ["nats://localhost:4222"]},
        "channels": [{"domain": "test", "channel": "test"}]
    }
    
    async with MockKrytenClient(config) as client:
        
        # Register handler
        responses = []
        
        @client.on("chatmsg")
        async def handler(event: ChatMessageEvent):
            if event.username != "EchoBot":
                responses.append(f"Echo: {event.message}")
        
        # Simulate event
        await client.simulate_event(
            "chatmsg",
            {
                "username": "Alice",
                "message": "Hello!",
                "time": 1234567890
            },
            channel="test",
            domain="test"
        )
        
        # Verify response
        assert len(responses) == 1
        assert responses[0] == "Echo: Hello!"

@pytest.mark.asyncio
async def test_command_bot():
    """Test command bot publishes correct commands."""
    
    config = {
        "nats": {"servers": ["nats://localhost:4222"]},
        "channels": [{"domain": "test", "channel": "test"}]
    }
    
    async with MockKrytenClient(config) as client:
        
        @client.on("chatmsg")
        async def handler(event: ChatMessageEvent):
            if event.message == "!skip":
                await client.voteskip(event.channel)
        
        # Simulate command
        await client.simulate_event(
            "chatmsg",
            {"username": "Bob", "message": "!skip", "time": 1234567890},
            channel="test"
        )
        
        # Check commands
        commands = client.get_published_commands()
        assert len(commands) == 1
        assert commands[0]["action"] == "voteskip"
```

### Integration Testing

Test with real NATS (requires server):

```python
import pytest
import asyncio
from kryten import KrytenClient

@pytest.mark.integration
@pytest.mark.asyncio
async def test_real_connection():
    """Test real NATS connection."""
    
    config = {
        "nats": {"servers": ["nats://localhost:4222"]},
        "channels": [{"domain": "test", "channel": "test"}]
    }
    
    async with KrytenClient(config) as client:
        assert client.is_connected
        
        # Send test message
        await client.send_chat("test", "Test message")
        
        # Wait briefly
        await asyncio.sleep(0.1)
```

Run integration tests:
```bash
pytest -m integration
```

## Deployment

### Running as Service

**systemd** (Linux):

Create `/etc/systemd/system/mybot.service`:
```ini
[Unit]
Description=My CyTube Bot
After=network.target

[Service]
Type=simple
User=botuser
WorkingDirectory=/home/botuser/mybot
Environment="NATS_SERVER=nats://localhost:4222"
Environment="NATS_USER=bot"
Environment="NATS_PASSWORD=secret"
ExecStart=/home/botuser/mybot/.venv/bin/python bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable mybot
sudo systemctl start mybot
sudo systemctl status mybot
```

### Docker

**Dockerfile**:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install Poetry
RUN pip install poetry

# Copy project files
COPY pyproject.toml poetry.lock ./
COPY bot.py ./
COPY config.json ./

# Install dependencies
RUN poetry install --no-dev

# Run bot
CMD ["poetry", "run", "python", "bot.py"]
```

**docker-compose.yml**:
```yaml
version: '3.8'

services:
  mybot:
    build: .
    restart: unless-stopped
    environment:
      - NATS_SERVER=nats://nats:4222
      - NATS_USER=bot
      - NATS_PASSWORD=secret
    depends_on:
      - nats
  
  nats:
    image: nats:latest
    ports:
      - "4222:4222"
```

Run:
```bash
docker-compose up -d
```

### Environment Variables

Production best practices:

```python
import os
from kryten import KrytenConfig

# Load from environment
config = {
    "nats": {
        "servers": [os.environ["NATS_SERVER"]],
        "user": os.environ.get("NATS_USER"),
        "password": os.environ.get("NATS_PASSWORD")
    },
    "channels": [
        {
            "domain": os.environ["CHANNEL_DOMAIN"],
            "channel": os.environ["CHANNEL_NAME"]
        }
    ]
}
```

### Logging

Production logging:

```python
import logging
import logging.handlers

# Rotating file handler
handler = logging.handlers.RotatingFileHandler(
    "bot.log",
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5
)
handler.setFormatter(logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
))

logger = logging.getLogger()
logger.addHandler(handler)
logger.setLevel(logging.INFO)
```

## Best Practices

### 1. Error Handling

Always wrap handlers in try-except:

```python
@client.on("chatmsg")
async def on_chat(event: ChatMessageEvent):
    try:
        # Your logic
        pass
    except Exception as e:
        logger.error(f"Error in handler: {e}", exc_info=True)
```

### 2. Rate Limiting

Don't spam the channel:

```python
import time
from collections import deque

class RateLimiter:
    def __init__(self, max_per_second=2):
        self.max_per_second = max_per_second
        self.timestamps = deque()
    
    def can_send(self):
        now = time.time()
        # Remove old timestamps
        while self.timestamps and self.timestamps[0] < now - 1:
            self.timestamps.popleft()
        
        if len(self.timestamps) < self.max_per_second:
            self.timestamps.append(now)
            return True
        return False

limiter = RateLimiter(max_per_second=2)

@client.on("chatmsg")
async def on_chat(event: ChatMessageEvent):
    if limiter.can_send():
        await client.send_chat(event.channel, "Response")
    else:
        logger.warning("Rate limit hit, message dropped")
```

### 3. Graceful Shutdown

Handle interrupts properly:

```python
import signal

shutdown_event = asyncio.Event()

def signal_handler(sig, frame):
    logger.info("Shutdown signal received")
    shutdown_event.set()

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

async def main():
    async with KrytenClient(config) as client:
        @client.on("chatmsg")
        async def handler(event):
            pass
        
        # Run until shutdown
        await shutdown_event.wait()
        logger.info("Shutting down gracefully...")
```

### 4. State Management

Persist state between restarts:

```python
import json

STATE_FILE = "bot_state.json"

def load_state():
    try:
        with open(STATE_FILE) as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_state(state):
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

# Load on startup
state = load_state()

# Save periodically
async def save_periodically():
    while True:
        await asyncio.sleep(300)  # Every 5 minutes
        save_state(state)
```

### 5. Monitoring

Track bot health:

```python
@client.on("chatmsg")
async def health_command(event: ChatMessageEvent):
    if event.message == "!health":
        health = client.health()
        await client.send_chat(
            event.channel,
            f"Status: {health.state} | "
            f"Uptime: {health.uptime:.0f}s | "
            f"Events: {health.events_received} | "
            f"Errors: {health.errors}"
        )
```

## Troubleshooting

### Bot Not Receiving Events

**Check**:
1. NATS server is running
2. Kryten Bridge is connected
3. Channel names match exactly
4. Bot has successfully connected (`client.is_connected`)

**Debug**:
```python
logging.basicConfig(level=logging.DEBUG)
```

### Commands Not Working

**Check**:
1. Command payload is correct
2. NATS connection is active
3. Check Kryten Bridge logs for errors

**Debug**:
```python
@client.on("chatmsg")
async def debug_command(event: ChatMessageEvent):
    if event.message == "!test":
        try:
            await client.send_chat(event.channel, "Test message")
            logger.info("Command sent successfully")
        except Exception as e:
            logger.error(f"Command failed: {e}", exc_info=True)
```

### Handler Not Triggering

**Check**:
1. Event name is correct (case-insensitive)
2. Channel/domain filters match
3. Handler is registered before `client.run()`

**Debug**:
```python
@client.on("chatmsg")
async def debug_handler(event):
    logger.info(f"Received event: {event}")
```

### Connection Issues

**Check**:
1. NATS server address is correct
2. Network connectivity
3. Authentication credentials (if required)

**Debug**:
```python
config = {
    "nats": {
        "servers": ["nats://localhost:4222"],
        "connect_timeout": 10.0,  # Increase timeout
        "max_reconnect_attempts": 5
    },
    ...
}
```

### Performance Issues

**Check**:
1. Handler timeout settings
2. Long-running operations in handlers
3. Memory leaks

**Optimize**:
```python
# Use asyncio for concurrent operations
@client.on("chatmsg")
async def on_chat(event: ChatMessageEvent):
    # Don't block
    asyncio.create_task(slow_operation(event))

async def slow_operation(event):
    # Long-running task
    await asyncio.sleep(10)
```

## Additional Resources

- **API Documentation**: See README.md
- **Library Development**: See DEVELOPER.md
- **GitHub Issues**: Report bugs and request features
- **Examples**: Check the `examples/` directory

---

**Happy Bot Building!** 🤖

If you have questions or need help, please open an issue on GitHub.

**Last Updated**: December 2025  
**Version**: 1.0
