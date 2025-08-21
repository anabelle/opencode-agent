# SCHEDULER

Overview
- Maintain a min-heap of canonical_targets keyed by next_run timestamp.
- Worker pool size = config.max_concurrency.
- On wake: pop all targets with next_run <= now, submit probe tasks up to concurrency limit.
- After probe completes, compute next_run = now + min(intervals_for_watchers, global_min_interval).
- Persist canonical_targets next_run to disk (with locking) to survive restarts.

Probe distribution
- Single probe per canonical target.
- For each watcher of that canonical target, attempt atomic consume and write watcher history.
- If consume fails (402), record CHECK_FAILED_CHARGE in ledger and continue.

Failure modes
- Probe timeout: record last_ok=False, still attempt consume (per policy).
- DB write contention: use file locks or switch to SQLite.
- Overload: if queue grows, increase next_run adaptively (backoff) and emit alert.

Tuning knobs
- max_concurrency
- min_interval
- per-host rate limit
- debt_policy: auto-pause watchers with zero balance
