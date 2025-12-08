# kryten-py API Completeness Audit
## Date: December 8, 2025

This document audits all CyTube Socket.IO commands implemented in **Kryten-Robot** vs **kryten-py** to ensure complete API coverage.

---

## ✅ COMPLETE COVERAGE - All Methods Implemented

### Chat & Messaging
| Socket.IO Event | Kryten-Robot Method | kryten-py Method | Status |
|----------------|---------------------|------------------|---------|
| `chatMsg` | `send_chat(message)` | `send_chat(channel, message)` | ✅ |
| `pm` | `send_pm(to, message)` | `send_pm(channel, username, message)` | ✅ |

### Playlist Management  
| Socket.IO Event | Kryten-Robot Method | kryten-py Method | Status |
|----------------|---------------------|------------------|---------|
| `queue` | `add_video(url, position, temp)` | `add_media(channel, type, id, position)` | ✅ |
| `delete` | `delete_video(uid)` | `delete_media(channel, uid)` | ✅ |
| `moveMedia` | `move_video(uid, after)` | `move_media(channel, uid, position)` | ✅ |
| `jumpTo` | `jump_to(uid)` | `jump_to(channel, uid)` | ✅ |
| `clearPlaylist` | `clear_playlist()` | `clear_playlist(channel)` | ✅ |
| `shufflePlaylist` | `shuffle_playlist()` | `shuffle_playlist(channel)` | ✅ |
| `setTemp` | `set_temp(uid, temp)` | `set_temp(channel, uid, is_temp)` | ✅ |
| `playNext` | `play_next()` | `play_next(channel)` | ✅ **PHASE 1** |

### Playback Control
| Socket.IO Event | Kryten-Robot Method | kryten-py Method | Status |
|----------------|---------------------|------------------|---------|
| `pause` | `pause()` | `pause(channel)` | ✅ |
| `play` | `play()` | `play(channel)` | ✅ |
| `seekTo` | `seek_to(time)` | `seek(channel, time_seconds)` | ✅ |

### Moderation (Rank 2+)
| Socket.IO Event | Kryten-Robot Method | kryten-py Method | Status |
|----------------|---------------------|------------------|---------|
| `kick` | `kick_user(username, reason)` | `kick_user(channel, username, reason)` | ✅ |
| `ban` | `ban_user(username, reason)` | `ban_user(channel, username, reason)` | ✅ |
| `voteskip` | `voteskip()` | `voteskip(channel)` | ✅ |
| `assignLeader` | `assign_leader(username)` | `assign_leader(channel, username)` | ✅ **PHASE 1** |
| `/mute` (via chat) | `mute_user(username)` | `mute_user(channel, username)` | ✅ **PHASE 1** |
| `/smute` (via chat) | `shadow_mute_user(username)` | `shadow_mute_user(channel, username)` | ✅ **PHASE 1** |
| `/unmute` (via chat) | `unmute_user(username)` | `unmute_user(channel, username)` | ✅ **PHASE 1** |

### Admin Functions (Rank 3+)
| Socket.IO Event | Kryten-Robot Method | kryten-py Method | Status |
|----------------|---------------------|------------------|---------|
| `setMotd` | `set_motd(motd)` | `set_motd(channel, motd)` | ✅ **PHASE 2** |
| `setChannelCSS` | `set_channel_css(css)` | `set_channel_css(channel, css)` | ✅ **PHASE 2** |
| `setChannelJS` | `set_channel_js(js)` | `set_channel_js(channel, js)` | ✅ **PHASE 2** |
| `setOptions` | `set_options(options)` | `set_options(channel, options)` | ✅ **PHASE 2** |
| `setPermissions` | `set_permissions(permissions)` | `set_permissions(channel, permissions)` | ✅ **PHASE 2** |
| `updateEmote` | `update_emote(name, image, source)` | `update_emote(channel, name, image, source)` | ✅ **PHASE 2** |
| `removeEmote` | `remove_emote(name)` | `remove_emote(channel, name)` | ✅ **PHASE 2** |
| `addFilter` | `add_filter(name, source, flags, replace, filterlinks, active)` | `add_filter(channel, name, source, flags, replace, filterlinks, active)` | ✅ **PHASE 2** |
| `updateFilter` | `update_filter(name, source, flags, replace, filterlinks, active)` | `update_filter(channel, name, source, flags, replace, filterlinks, active)` | ✅ **PHASE 2** |
| `removeFilter` | `remove_filter(name)` | `remove_filter(channel, name)` | ✅ **PHASE 2** |

### Poll Management (Rank 2+)
| Socket.IO Event | Kryten-Robot Method | kryten-py Method | Status |
|----------------|---------------------|------------------|---------|
| `newPoll` | `new_poll(title, options, obscured, timeout)` | `new_poll(channel, title, options, obscured, timeout)` | ✅ **PHASE 3** |
| `vote` | `vote(option)` | `vote(channel, option)` | ✅ **PHASE 3** |
| `closePoll` | `close_poll()` | `close_poll(channel)` | ✅ **PHASE 3** |

### Channel Administration (Rank 3-4+)
| Socket.IO Event | Kryten-Robot Method | kryten-py Method | Status |
|----------------|---------------------|------------------|---------|
| `setChannelRank` | `set_channel_rank(username, rank)` | `set_channel_rank(channel, username, rank)` | ✅ **PHASE 3** |
| `requestChannelRanks` | `request_channel_ranks()` | `request_channel_ranks(channel)` | ✅ **PHASE 3** |
| `requestBanlist` | `request_banlist()` | `request_banlist(channel)` | ✅ **PHASE 3** |
| `unban` | `unban(ban_id)` | `unban(channel, ban_id)` | ✅ **PHASE 3** |
| `readChanLog` | `read_chan_log(count)` | `read_chan_log(channel, count)` | ✅ **PHASE 3** |

### Library Management
| Socket.IO Event | Kryten-Robot Method | kryten-py Method | Status |
|----------------|---------------------|------------------|---------|
| `searchMedia` | `search_library(query, source)` | `search_library(channel, query, source)` | ✅ **PHASE 3** |
| `uncache` | `delete_from_library(media_id)` | `delete_from_library(channel, media_id)` | ✅ **PHASE 3** |

---

## 🔍 METHOD SIGNATURE DISCREPANCIES

### Issue: Parameter Naming Differences

Some parameters don't match between Kryten-Robot and kryten-py:

#### 1. **assign_leader** Parameter Mismatch
- **Kryten-Robot**: `data={"name": username}`  
- **kryten-py**: `data={"username": username}` ❌ **MISMATCH**
- **CyTube expects**: `{"name": "username"}` according to Kryten-Robot implementation

#### 2. **mute_user/shadow_mute_user/unmute_user** Parameter Mismatch  
- **Kryten-Robot**: Uses chat commands `/mute`, `/smute`, `/unmute` via `chatMsg`
- **kryten-py**: `data={"username": username}` ❌ **WRONG APPROACH**
- **Should be**: Using chat commands via `chatMsg` like Kryten-Robot does

#### 3. **unban** Parameter Mismatch
- **Kryten-Robot**: `data={"id": ban_id}`
- **kryten-py**: `data={"ban_id": ban_id}` ❌ **MISMATCH**
- **CyTube expects**: `{"id": ban_id}` according to Kryten-Robot implementation

#### 4. **search_library** Action Name Mismatch  
- **Kryten-Robot**: Emits `searchMedia` event
- **kryten-py**: Action is `searchLibrary` ❌ **MISMATCH**
- **Should be**: `searchMedia`

#### 5. **delete_from_library** Action + Parameter Mismatch
- **Kryten-Robot**: Emits `uncache` with `data={"id": media_id}`
- **kryten-py**: Action is `deleteFromLibrary` with `data={"media_id": media_id}` ❌ **DOUBLE MISMATCH**
- **Should be**: Action `uncache` with `{"id": media_id}`

#### 6. **new_poll** Parameter Mismatch
- **Kryten-Robot**: `data={"title": ..., "opts": options, ...}`
- **kryten-py**: `data={"title": ..., "options": options, ...}` ❌ **MISMATCH**
- **CyTube expects**: `opts` not `options`

---

## 🎯 BONUS FEATURES IN kryten-py

### Rank-Checking Helper Methods
kryten-py includes convenience methods not in Kryten-Robot:

1. **`get_user_level(channel)`** - Query bot's current rank ✅ **ADDED TODAY**
2. **`_check_rank(channel, required_rank, operation)`** - Internal rank verification
3. **`safe_assign_leader(channel, username)`** - Auto-checks rank before executing

These are **additions** that enhance the library but aren't in Kryten-Robot.

---

## 📋 RECOMMENDATIONS

### Critical Fixes Required

1. **Fix `assign_leader` parameter**: Change `username` → `name`
2. **Fix mute commands**: Implement via chat commands like Kryten-Robot
3. **Fix `unban` parameter**: Change `ban_id` → `id`
4. **Fix `search_library` action**: Change `searchLibrary` → `searchMedia`
5. **Fix `delete_from_library`**: Change action to `uncache` and parameter to `id`
6. **Fix `new_poll` parameter**: Change `options` → `opts`

### Command Subscriber Compatibility

The `CommandSubscriber` in Kryten-Robot supports both naming conventions:
- `assignLeader` or `assign_leader`
- `setMotd` or `set_motd`
- etc.

This ensures backward compatibility. kryten-py should ensure it publishes the **correct Socket.IO event names** that CyTube expects, NOT the Python-friendly names.

---

## ✅ CONCLUSION

**Total Commands**: 31 methods  
**Implemented in kryten-py**: 31 methods ✅  
**Correct Implementation**: 25 methods ✅  
**Need Fixing**: 6 methods ❌

**Overall Coverage**: 100% (all commands exist)  
**Correctness**: 81% (6 parameter/action name mismatches)

The API is **functionally complete** but has **critical correctness issues** that will cause failures when commands reach CyTube. All commands exist, but 6 need parameter/action name fixes to match what CyTube actually expects.
