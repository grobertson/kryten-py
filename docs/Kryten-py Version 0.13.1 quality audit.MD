## Kryten-Py Library Survey Report

### 1. What It Is

**kryten-py** (v0.16.1) is the foundational Python library for building CyTube microservices within the Kryten ecosystem. It provides a NATS-based client (`KrytenClient`) for communicating with CyTube via the Kryten bridge. It is the **only library used across all other services** — every service that interacts with CyTube imports it.

### 2. File Size Analysis

| File | Size | % of Library | Notes |
|------|------|-------------|-------|
| `client.py` | **136 KB** | **62%** | Single file containing KrytenClient, all command methods, event subscription, lifecycle wiring, and sync request-reply wrappers |
| `mock.py` | 23 KB | 10% | MockKrytenClient for testing |
| `lifecycle_events.py` | 18 KB | 8% | LifecycleEventPublisher |
| `metrics_server.py` | 10 KB | 5% | BaseMetricsServer + SimpleMetricsServer |
| `subject_builder.py` | 11 KB | 5% | NATS subject builder |
| `config.py` | 11 KB | 5% | Pydantic config models |
| `kv_store.py` | 9 KB | 4% | KV store helpers |
| `models.py` | 5 KB | 2% | Event models |
| `health.py` | 2 KB | 1% | Health status models |
| `exceptions.py` | 0.7 KB | <1% | Exception hierarchy |
| `__init__.py` | 3 KB | 1% | Public API exports |

### 3. Key Findings

#### A. `client.py` (136 KB, 3,951 lines) — **DOMINANT FILE CONCERN**
This single file handles: configuration parsing, NATS connection/reconnection, event handler registration, event dispatching, subscription management, lifecycle publisher wiring, all command methods (~70+ methods), request-reply wrappers, rank checking, and health status. It's 62% of the entire library.

The command methods alone occupy ~3,000 lines and are organized into phases:
- Chat commands: `send_chat`, `send_pm`, `send_command` 
- Playlist commands: `add_media`, `delete_media`, `move_media`, `jump_to`, `clear_playlist`, `shuffle_playlist`, `set_temp`
- Playback commands: `pause`, `play`, `seek`
- Moderation commands: `kick_user`, `ban_user`, `mute_user`, `shadow_mute_user`, `unmute_user`, `assign_leader`, `voteskip`, `play_next`
- Admin commands: `set_motd`, `set_channel_css`, `set_channel_js`, `set_options`, `set_permissions`, `update_emote`, `remove_emote`, `add_filter`, `update_filter`, `remove_filter`
- Poll commands: `new_poll`, `vote`, `close_poll`
- Channel rank commands: `set_channel_rank`, `request_channel_ranks`, `safe_set_channel_rank`
- Request-reply wrappers: `get_banlist`, `get_channel_ranks`, `get_chan_log`, `get_library_search`

**Recommendation**: Split into:
- `client/__init__.py` — KrytenClient class core (connect, run, stop, disconnect, event handlers)
- `client/commands_chat.py` — send_chat, send_pm, send_command
- `client/commands_playlist.py` — add, delete, move, jump, clear, shuffle, set_temp
- `client/commands_moderation.py` — kick, ban, mute, leader, voteskip, play_next
- `client/commands_admin.py` — MOTD, CSS, JS, options, permissions, emotes, filters, polls, rank
- `client/requests.py` — get_banlist, get_channel_ranks, get_chan_log, get_library_search, nats_request

#### B. `__send_command` (client.py:589-659) vs `send_command` (client.py:561-587) — **CODE DUPLICATION**
`send_command` is a thin public wrapper that calls `__send_command` with the same signature. The double-underscore method is 70 lines of hand-crafted JSON. Both methods serve the same purpose — the private method is directly called by every command method throughout the file. The public wrapper could simply be eliminated or both could be merged.

#### C. `subject_builder.py` — **DUPLICATED COMMAND SUBJECT FORMAT**
`build_command_subject()` (line 197) generates `kryten.{service}.command` format, but `client.py.__send_command()` (line 623) also hard-codes `subject = build_command_subject(service)`. Meanwhile `mock.py._record_command()` (line 673) uses its own subject format `{service}.commands.{channel}.{action}`. This inconsistency means the mock records are formatted differently from real commands — tests using `get_published_commands()` will see mismatched subject strings.

#### D. `subject_builder.py:sanitize_token()` (line 119-125) — **DEPRECATED ALIAS**
Explicitly marked as a deprecated alias for `normalize_token`. Exported in `__all__` and via `__init__.py`. Remove in next major version.

#### E. `client.py:assign_leader()` (lines 981-1012) — **INCORRECT COMMAND TYPE**
Uses `assignLeader` with body `{"name": username}`, which is the `setLeader` CyTube command. Should use `"setLeader"` as the command type for consistency with the bot's expectations.

#### F. `mock.py` (690 lines) — **DUPLICATES MOST OF KRyTENCLIENT INTERFACE**
`MockKrytenClient` reimplements the full KrytenClient interface with in-memory state. While necessary for testing, it duplicates ~40 methods. This is intentional for test isolation, but worth noting for maintenance: when adding a new command to `client.py`, `mock.py` must also be updated.

#### G. Unused/Dead Code Patterns

- **`client.py` lines 1982-2000**: `_check_rank()` method defined but never called from anywhere in the client. It's a helper that checks rank with an empty implementation below.
- **`lifecycle_events.py`**: `publish_connected()` and `publish_disconnected()` methods (lines 374-414) are defined but never called within the library. KrytenClient.connect() never calls them — they're only available for external consumers who may or may not use them.
- **`metrics_server.py:BaseMetricsServer`**: The `client` parameter (line 63) stores a reference but it's only used to check `getattr(self.client, "_running", False)` for NATS status. With `SimpleMetricsServer` existing as a callback-based alternative, `BaseMetricsServer` could potentially be simplified.

### 4. Cross-Workspace Usage

All other services depend on kryten-py as the NATS transport layer:

| Workspace | Uses kryten-py? | How |
|-----------|----------------|-----|
| kryten-api-gate | **No** | Does not import kryten-py directly (uses HTTP client, not NATS) |
| kryten-py (self) | — | Source of the library |
| kryten-cli | **No** | CLI tool, separate from microservice pattern |
| Kryten-Robot | **No** | Each query returned 0 results. Kryten-Robot likely communicates via NATS subjects or direct CyTube bridge rather than the Python library wrapper |
| kryten-webqueue | **No** | Communicates with api-gate via HTTP, not via NATS client |
| kryten-economy | **No** | `KrytenClient` is referenced in TypeChecking guards, but the actual import is from the installed package at runtime, not from workspace source |

This means kryten-py is **lightly used** within the workspace itself — most consumers use it as an installed package dependency. The library's primary internal consumer for testing is `mock.py` and the test suite.

### 5. Summary of Recommendations

| Priority | Recommendation | Effort | Impact |
|----------|---------------|--------|--------|
| **High** | Split `client.py` (136 KB) into sub-modules: commands_chat, commands_playlist, commands_moderation, commands_admin, requests | 1-2 days | Major — reduces cognitive load for the 62% file |
| **Medium** | Merge `send_command` / `__send_command` to eliminate the thin public wrapper | 30 min | Minor cleanup |
| **Medium** | Fix subject format inconsistency between `client.py` (kryten.{service}.command) and `mock.py` ({service}.commands.{channel}.{action}) | 1 hour | Prevents test confusion |
| **Medium** | Fix `assign_leader` command type from `assignLeader` to `setLeader` | 15 min | Minor bug fix |
| **Low** | Remove deprecated `sanitize_token()` alias | 5 min | Cleanup |
| **Low** | Either remove or wire up `publish_connected`/`publish_disconnected` in lifecycle_events | 30 min | Clarity |
| **Low** | Either remove or wire up `_check_rank()` in client.py | 15 min | Remove dead code |

### 6. Overall Assessment

The kryten-py library is **well-designed, well-documented, and cleanly architected** at the module level. The single major issue is that `client.py` has grown to 136 KB / 3,951 lines by accumulating every command method as the ecosystem has expanded. All methods follow the same consistent pattern (wrapper → `__send_command` → NATS publish), making them easy to extract into focused sub-modules. The `MockKrytenClient` in `mock.py` provides excellent test isolation. No actual dead code requiring urgent removal was found — only minor orphaned helpers and a deprecated function alias.