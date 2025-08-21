# ARCHITECTURE

Overview
- Sessionless, token-based UX: session_token (bearer) maps to a lightweight session that holds credits and watchers.
- Canonical targets: single canonical probe per unique normalized target; multiple watchers reference the canonical target.
- Checker scheduler: central scheduler runs probes for canonical targets, distributes result to watchers, and charges each watcher.

Components
- API (FastAPI): endpoints for session creation/topup/register targets, admin endpoints, ledger/receipts.
- Scheduler: in-process priority queue + worker pool that runs probes and enqueues next runs.
- Checker worker: executes probe (curl/socket) and records result.
- Persistence: file-per-session and append-only ledger (initially JSON + log); migrate to SQLite when scaling.
- Proxy: nginx terminates TLS and proxies to API.

Data flow
1. User tops up -> session_token created -> dashboard reachable at /d/<token>
2. User registers target -> server canonicalizes -> creates watcher linking session_token to canonical target
3. Scheduler schedules canonical probe -> worker performs probe -> result stored on canonical target
4. For each watcher: checker attempts consume(session_token, watcher_id), ledger append, per-watcher history write

Rationale
- Low friction UX while retaining grouping via session tokens.
- Single probe per canonical target avoids redundant network load.
- Per-watcher billing maximizes revenue and is simple to reason about.

Notes
- All writes to shared state must use file locking or SQLite to avoid races.
- Earnings are recorded in append-only ledger for auditability.
