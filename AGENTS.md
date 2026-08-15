# kryten-py — Project Guidelines

kryten-py is the **shared client library** for the Kryten ecosystem — not a service. It provides `KrytenClient` (a NATS client wrapper), KV-store helpers, service lifecycle/heartbeat, health checks, the NATS subject builder, and a mock client for tests. **Every Kryten service depends on this package**, so API stability and backward compatibility are the top priority.

## Architecture
- This is a **library**: no NATS command subject, no config auto-discovery, no systemd unit, no service loop. Do not add service-style scaffolding here.
- Public surface consumed by services: `KrytenClient` (connect, `@client.on(...)` event subscriptions, `send_command`/`nats_request`, health/lifecycle), KV helpers (`get_kv_store`, `get_or_create_kv_store`, `kv_get`/`kv_put`/`kv_delete`), and the subject builder (normalizes `kryten.events.{domain}.{channel}.{event}` — lowercase, dots stripped).
- The library defines the ecosystem's contracts. Keep these docs authoritative and in sync with the code: [COMMAND_PROTOCOL.md](COMMAND_PROTOCOL.md), [LIBRARY_REFERENCE.md](LIBRARY_REFERENCE.md), [STATE_MANAGEMENT.md](STATE_MANAGEMENT.md), [ERROR_HANDLING.md](ERROR_HANDLING.md), [DEPLOYMENT_AND_MONITORING.md](DEPLOYMENT_AND_MONITORING.md). Ecosystem overview: [../KRYTEN_ARCHITECTURE.md](../KRYTEN_ARCHITECTURE.md).

## Build, Test & Conventions
Shared tooling and repo rules (uv build/test, versioning, CHANGELOG, commit style):
see [../KRYTEN_CONVENTIONS.md](../KRYTEN_CONVENTIONS.md). This is a **library**, so
several ecosystem service-conventions do NOT apply (no command subject, no config
auto-discovery, no service loop). Repo specifics:
- Python 3.10+ (must support the lowest version used by any consuming service),
  `src/` layout (`src/kryten/`); mypy target `uv run mypy src/kryten`.
- **Backward compatibility is a hard requirement.** Any change to a public method
  signature, event/command shape, KV helper behavior, or subject-normalization
  rule can break every downstream service.
  - Prefer additive changes. Deprecate before removing; keep deprecated paths
    working across at least one minor release.
  - Breaking changes require a **major** version bump (SemVer), a `CHANGELOG.md`
    entry, updated protocol docs, and a migration note listing affected services.
- Keep the mock client in lockstep with the real client so service test suites stay valid.
