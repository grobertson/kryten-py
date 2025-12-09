# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.5.6] - 2025-12-09

### Changed

- **Compatibility**: Lowered minimum Python version requirement from 3.11 to 3.10
  - No Python 3.11+ specific features are used in the codebase
  - Dependencies (pydantic ≥3.9, nats-py ≥3.7) support Python 3.10
  - Updated tooling configuration (black, ruff, mypy) to target Python 3.10

## [0.5.5] - 2025-12-09

### Fixed

- **Documentation**: Added missing moderation methods to README API reference
  - `mute_user()` - Mute user from chatting (rank 2+)
  - `shadow_mute_user()` - Shadow mute user (only mods see messages, rank 2+)
  - `unmute_user()` - Remove mute/shadow mute (rank 2+)
  - `assign_leader()` - Give/remove leader status (rank 2+)
  - `play_next()` - Skip to next video immediately (rank 2+)
  - These methods have always been functional, just undocumented in the main README

## [0.5.4] - 2025-12-09

### Fixed

- **Documentation**: Removed anti-pattern of importing `nats` directly in README examples
  - All Lifecycle Events examples now use `client._nats` instead of `import nats`
  - All KeyValue Store examples now use `client.kv_*` methods instead of standalone helpers
  - Monitoring examples updated to use KrytenClient context
  - Users should never import `nats` directly - always use KrytenClient's built-in methods

## [0.4.0] - 2025-12-08

### Changed - BREAKING

- **Subject Format Redesign**: Complete overhaul of NATS subject structure for robustness
  - Changed prefix from `cytube.*` to `kryten.*` for better namespace clarity
  - Events: `kryten.events.cytube.{channel}.{event}` (was `cytube.events.{domain}.{channel}.{event}`)
  - Commands: `kryten.commands.cytube.{channel}.{action}` (was `cytube.commands.{domain}.{channel}.{action}`)
  - Domain variations (cy.tube, cytu.be, Cytu.BE) all normalize to "cytube" literal
  - Channels normalized: lowercase, dots removed, spaces to hyphens
  - **This is case-insensitive**: "420Grindhouse" and "420grindhouse" match the same subject

- **Aggressive Normalization**: New `normalize_token()` function replaces domain-specific logic
  - Removes ALL dots from domains/channels (cy.tube → cytube)
  - Lowercase everything
  - Consistent matching regardless of input variations

### Fixed

- Eliminated case-sensitivity brittleness in NATS subjects
- Domain dot variations no longer cause routing failures
- Commands now reliably reach intended channels

### Migration Required

**Kryten-Robot must be updated** to match the new subject format. Both kryten-py and Kryten-Robot subject_builder.py files must use the same logic.

## [0.3.4] - 2025-12-08

### Fixed

- **Command Subject Builder**: Fixed `build_command_subject()` to preserve dots in domain names (e.g., `cy.tube`)
  - Previously sanitized domain which removed dots, breaking commands to domains with dots
  - Now matches event subject behavior by only lowercasing domain, preserving dots
  - Fixes issue where commands to `cy.tube` were sent to `cytube` instead

## [0.3.3] - 2025-12-06

### Added

- **KrytenClient KV Store Methods**: Added high-level KeyValue store methods to KrytenClient class
  - `get_kv_bucket(bucket_name)` - Get or create a KV bucket
  - `kv_get(bucket_name, key, default, parse_json)` - Get value from KV store
  - `kv_put(bucket_name, key, value, as_json)` - Put value into KV store
  - `kv_delete(bucket_name, key)` - Delete key from KV store
  - `kv_keys(bucket_name)` - List all keys in bucket
  - `kv_get_all(bucket_name, parse_json)` - Get all key-value pairs

### Changed

- KV store operations now accessible directly through KrytenClient without needing separate NATS connection
- Microservices can now use only KrytenClient for all NATS interactions (no direct nats-py imports needed)

## [0.3.1] - 2025-12-06

### Changed

- **Documentation**: Updated README.md with comprehensive documentation for new features
  - Added "Lifecycle Events" section with usage examples and monitoring patterns
  - Added "KeyValue Store" section with basic operations, JSON serialization, and bulk operations
  - Updated feature list to highlight lifecycle events and KV store capabilities
  - Added reference to `lifecycle_and_kv_example.py` in examples section

## [0.3.0] - 2025-12-06

### Added

- **Lifecycle Events**: New `LifecycleEventPublisher` class for service lifecycle management
  - Publish startup/shutdown events
  - Publish connection/disconnection events
  - Subscribe to groupwide restart notices
  - Includes service metadata (version, hostname, uptime)
- **KeyValue Store Helpers**: New `kv_store` module with utility functions for NATS JetStream KV stores
  - `get_kv_store()`: Get or create KV bucket
  - `kv_get()`: Get value with optional JSON parsing
  - `kv_put()`: Put value with optional JSON serialization
  - `kv_delete()`: Delete key from store
  - `kv_keys()`: List all keys in store
  - `kv_get_all()`: Get all key-value pairs

### Changed
- Updated version to 0.3.0 for new feature release

## [0.2.3] - 2025-12-05

### Fixed

- **Command Subject**: Fixed NATS command subject to include domain (`cytube.commands.{domain}.{channel}.{action}`) to match Kryten bridge subscription pattern

## [0.2.2] - 2025-12-05

### Fixed
- Fixed PM command to send `message` parameter (not `msg`) to match Kryten bridge's `send_pm()` function signature

## [0.2.1] - 2025-12-05

### Fixed
- **PM Command**: Changed PM message field from `"message"` to `"msg"` to match CyTube Socket.IO expectations
- **Payload Type**: Updated `RawEvent.payload` to accept any type, not just dictionaries
- **Event Conversion**: Added type check to skip conversion for non-dict payloads

### Removed
- **NATS Config**: Removed unsupported `max_pending_size` parameter from NATS connection

## [0.2.0] - 2024-12-04

### Added
- **Typed Event Conversion**: Automatic conversion of `RawEvent` to specific typed event models
  - `ChatMessageEvent` for chat messages and PMs
  - `UserJoinEvent` for user joins
  - `UserLeaveEvent` for user leaves
  - `ChangeMediaEvent` for media changes
  - `PlaylistUpdateEvent` for playlist updates
- Flexible payload parsing supporting both nested CyTube format and flat test format
- Support for both "msg" and "message" field names in chat events
- Comprehensive test suite for event conversion (`test_event_conversion.py`)
- Fallback to `RawEvent` for unknown event types (backward compatible)

### Changed
- Event handlers now receive typed event objects instead of `RawEvent`
- `MockKrytenClient` mirrors event conversion behavior for consistent testing
- Updated echo bot example to use typed `ChatMessageEvent` attributes

### Fixed
- Username extraction now handles both nested `{user: {name, rank}}` and flat `{username, rank}` structures
- PM events properly converted to `ChatMessageEvent`

## [0.1.0] - 2024-12-01

### Added
- Initial release of kryten-py
- Core `KrytenClient` for CyTube interaction via NATS
- Event handler registration with `@client.on()` decorator
- Channel and domain filtering for event handlers
- Comprehensive command API:
  - Chat commands: `send_chat()`, `send_pm()`
  - Playlist commands: `add_media()`, `delete_media()`, `move_media()`, `jump_to()`, `clear_playlist()`, `shuffle_playlist()`, `set_temp()`
  - Playback commands: `pause()`, `play()`, `seek()`
  - Moderation commands: `kick_user()`, `ban_user()`, `voteskip()`
- Health monitoring and metrics (`health()`, `channels`)
- `MockKrytenClient` for testing without NATS connection
- Connection management with async context manager support
- Configurable retry logic with exponential backoff
- NATS reconnection handling
- Pydantic-based configuration validation
- Comprehensive test suite (51 tests, 58% coverage)

### Documentation
- README with quickstart guide and examples
- API documentation for all public methods
- Configuration guide (CONFIG.md)
- Implementation notes (IMPLEMENTATION_NOTES.md)
- Echo bot example application

[0.2.0]: https://github.com/yourusername/kryten-py/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/yourusername/kryten-py/releases/tag/v0.1.0
