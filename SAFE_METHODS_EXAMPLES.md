# Safe Methods with Auto-Rank Checking - Usage Examples

## Overview

The kryten-py client now includes "safe" convenience methods that automatically check your bot's rank before executing privileged operations. These methods prevent errors and provide clear feedback about permission issues.

## Available Safe Methods

| Method | Required Rank | Description |
|--------|---------------|-------------|
| `safe_assign_leader()` | 2+ (Moderator) | Give/remove leader status |
| `safe_set_motd()` | 3+ (Admin) | Set message of the day |
| `safe_set_channel_rank()` | 4+ (Owner) | Change user's permanent rank |
| `safe_update_emote()` | 3+ (Admin) | Add/update channel emote |
| `safe_add_filter()` | 3+ (Admin) | Add chat filter |
| `safe_set_options()` | 3+ (Admin) | Update channel options |

## Return Format

All safe methods return a dictionary with:
- `success` (bool): Whether the operation succeeded
- `message_id` (str): NATS message ID if successful
- `error` (str): Error description if failed
- `rank` (int): Current bot rank (only on rank errors)

## Basic Usage

### Example 1: Setting MOTD Safely

```python
from kryten import KrytenClient

async def update_welcome_message():
    client = KrytenClient(config)
    await client.connect()
    
    # Attempt to set MOTD (requires rank 3+)
    result = await client.safe_set_motd(
        channel="lounge",
        motd="<h1>Welcome to the lounge!</h1>"
    )
    
    if result["success"]:
        print(f"✅ MOTD updated successfully!")
        print(f"Message ID: {result['message_id']}")
    else:
        print(f"❌ Failed to update MOTD: {result['error']}")
        if "rank" in result:
            print(f"Your rank: {result['rank']}, need: 3+")
    
    await client.close()
```

**Output if bot has rank 2:**
```
❌ Failed to update MOTD: Insufficient rank: need 3+, have 2
Your rank: 2, need: 3+
```

**Output if bot has rank 3+:**
```
✅ MOTD updated successfully!
Message ID: nats-msg-xyz123
```

### Example 2: Promoting Users Safely

```python
async def promote_moderator(username: str):
    client = KrytenClient(config)
    await client.connect()
    
    # Attempt to promote user to moderator (requires rank 4+)
    result = await client.safe_set_channel_rank(
        channel="lounge",
        username=username,
        rank=2  # Moderator
    )
    
    if result["success"]:
        print(f"✅ {username} is now a moderator!")
    else:
        print(f"❌ Cannot promote {username}: {result['error']}")
    
    await client.close()
```

### Example 3: Managing Emotes Safely

```python
async def add_custom_emote():
    client = KrytenClient(config)
    await client.connect()
    
    # Add custom emote (requires rank 3+)
    result = await client.safe_update_emote(
        channel="lounge",
        name="CustomKappa",
        image="abc123xyz",
        source="imgur"
    )
    
    if result["success"]:
        print("✅ Emote added! Users can now use :CustomKappa:")
    else:
        print(f"❌ Emote addition failed: {result['error']}")
    
    await client.close()
```

## Advanced Usage

### Example 4: Graceful Degradation

```python
async def configure_channel_with_fallback():
    """Try admin operations, fall back to basic operations if insufficient rank."""
    client = KrytenClient(config)
    await client.connect()
    
    # Try to set advanced options
    result = await client.safe_set_options(
        channel="lounge",
        options={
            "allow_voteskip": True,
            "voteskip_ratio": 0.5,
            "afk_timeout": 600
        }
    )
    
    if result["success"]:
        print("✅ Full channel configuration applied")
    elif "Insufficient rank" in result["error"]:
        print("⚠️  Bot lacks admin rank, using basic features only")
        # Fall back to operations that don't require admin
        await client.send_chat("lounge", "Running with limited permissions")
    else:
        print(f"❌ Configuration failed: {result['error']}")
    
    await client.close()
```

### Example 5: Batch Operations with Rank Validation

```python
async def setup_channel_filters():
    """Add multiple chat filters, checking rank once."""
    client = KrytenClient(config)
    await client.connect()
    
    filters = [
        {"name": "profanity1", "source": r"\bbad\b", "flags": "gi", "replace": "***"},
        {"name": "profanity2", "source": r"\bworse\b", "flags": "gi", "replace": "***"},
        {"name": "spam", "source": r"http://spam\.com", "flags": "gi", "replace": "[link removed]"},
    ]
    
    # Check rank once
    first_result = await client.safe_add_filter(
        channel="lounge",
        **filters[0]
    )
    
    if not first_result["success"]:
        print(f"❌ Cannot add filters: {first_result['error']}")
        return
    
    print(f"✅ Filter '{filters[0]['name']}' added")
    
    # We know we have rank 3+, skip check for remaining filters
    for filter_def in filters[1:]:
        result = await client.safe_add_filter(
            channel="lounge",
            check_rank=False,  # Skip rank check for performance
            **filter_def
        )
        if result["success"]:
            print(f"✅ Filter '{filter_def['name']}' added")
        else:
            print(f"❌ Failed to add '{filter_def['name']}': {result['error']}")
    
    await client.close()
```

### Example 6: Interactive Bot Command

```python
async def handle_promote_command(channel: str, requester: str, target: str):
    """Bot command: !promote <username>"""
    client = KrytenClient(config)
    await client.connect()
    
    # Try to promote target user
    result = await client.safe_set_channel_rank(
        channel=channel,
        username=target,
        rank=2  # Moderator
    )
    
    if result["success"]:
        await client.send_chat(
            channel,
            f"@{requester} Successfully promoted {target} to moderator!"
        )
    elif "Insufficient rank" in result["error"]:
        await client.send_chat(
            channel,
            f"@{requester} Sorry, I don't have owner permissions to promote users. "
            f"(My rank: {result.get('rank', 0)})"
        )
    else:
        await client.send_chat(
            channel,
            f"@{requester} Promotion failed: {result['error']}"
        )
    
    await client.close()
```

## Comparison: Regular vs Safe Methods

### Regular Methods (Direct)
```python
# Regular method - no rank checking
try:
    msg_id = await client.set_motd("lounge", "<h1>Welcome</h1>")
    print(f"Success: {msg_id}")
except Exception as e:
    # Will fail silently or with generic error if rank insufficient
    print(f"Failed: {e}")
```

**Pros:**
- Slightly faster (no rank check overhead)
- Simpler for scripts where rank is known

**Cons:**
- No pre-validation
- Unclear why operation failed
- Requires manual rank checking

### Safe Methods (Rank-Checked)
```python
# Safe method - automatic rank checking
result = await client.safe_set_motd("lounge", "<h1>Welcome</h1>")
if result["success"]:
    print(f"Success: {result['message_id']}")
else:
    print(f"Failed: {result['error']}")
    if "rank" in result:
        print(f"Need rank 3+, have {result['rank']}")
```

**Pros:**
- Clear error messages
- Pre-validated before sending command
- Graceful handling of permission issues
- Better for production bots

**Cons:**
- Slight overhead (NATS query for rank)
- Extra network round-trip

## Best Practices

### 1. Use Safe Methods in Production

For production bots where permissions may vary:
```python
result = await client.safe_set_motd(channel, motd)
if not result["success"]:
    log.warning(f"MOTD update failed: {result['error']}")
```

### 2. Cache Rank Check for Batch Operations

When performing multiple operations:
```python
# Check once
first_result = await client.safe_update_emote(...)
if not first_result["success"]:
    return  # Don't proceed

# Skip checks for subsequent operations
for emote in remaining_emotes:
    await client.safe_update_emote(..., check_rank=False)
```

### 3. Provide User Feedback

For interactive bots:
```python
result = await client.safe_add_filter(channel, ...)
if "Insufficient rank" in result.get("error", ""):
    await client.send_chat(
        channel,
        "Sorry, I need admin rank to manage filters!"
    )
```

### 4. Skip Check When Rank is Known

For administrative scripts where bot rank is guaranteed:
```python
# Deployment script - bot is known to be owner
result = await client.safe_set_options(
    channel,
    options,
    check_rank=False  # Skip check, we know we're owner
)
```

## Error Handling Patterns

### Pattern 1: Simple Success/Failure
```python
result = await client.safe_set_motd(channel, motd)
if result["success"]:
    print("✅ Done")
else:
    print(f"❌ Error: {result['error']}")
```

### Pattern 2: Rank-Specific Handling
```python
result = await client.safe_set_channel_rank(channel, user, 2)
if result["success"]:
    notify_promotion(user)
elif "Insufficient rank" in result["error"]:
    log.warning(f"Bot lacks owner rank: {result.get('rank', 0)}")
else:
    log.error(f"Promotion failed: {result['error']}")
```

### Pattern 3: Retry with Fallback
```python
result = await client.safe_set_options(channel, advanced_options)
if not result["success"] and "Insufficient rank" in result["error"]:
    # Fall back to basic options that don't require admin
    await client.set_playlist_lock(channel, False)  # Rank 2+
```

## Integration with Existing Code

Safe methods are drop-in compatible. Migrate gradually:

### Before (Regular Methods)
```python
try:
    await client.set_motd(channel, motd)
    print("Updated MOTD")
except Exception as e:
    print(f"Failed: {e}")
```

### After (Safe Methods)
```python
result = await client.safe_set_motd(channel, motd)
if result["success"]:
    print("Updated MOTD")
else:
    print(f"Failed: {result['error']}")
```

## Performance Considerations

Each safe method makes one additional NATS request to check rank (~10-50ms overhead). For batch operations:

```python
# ❌ Inefficient - checks rank 100 times
for emote in emotes:
    await client.safe_update_emote(channel, emote.name, emote.image)

# ✅ Efficient - checks rank once
first = emotes[0]
result = await client.safe_update_emote(channel, first.name, first.image)
if result["success"]:
    for emote in emotes[1:]:
        await client.safe_update_emote(
            channel, emote.name, emote.image, check_rank=False
        )
```

## Conclusion

Safe methods provide:
- ✅ Automatic rank validation
- ✅ Clear error messages
- ✅ Graceful permission handling
- ✅ Better user experience

Use them whenever:
- Bot permissions may vary
- Running in production
- Providing interactive features
- Building user-facing commands

Skip rank checks when:
- Batch processing after initial validation
- Bot rank is guaranteed (deployment scripts)
- Performance is critical and rank is known
