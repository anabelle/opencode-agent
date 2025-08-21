# DATA_SCHEMA

JSON model (file-based MVP)

- /home/ubuntu/monitor/sessions/<session_token>.json
{
  "session_token": "<token>",
  "credits": 1000,
  "created_at": 1234567890.0,
  "last_used": 1234567890.0,
  "expires_at": 1234567890.0,
  "meta": {"label":"my monitors"}
}

- /home/ubuntu/monitor/canonical_targets.json (list)
[
  {"cid":"c1","fingerprint":"sha256(...)","url":"https://example.com","probe_type":"http","last_probe":1234567.0,"last_ok":true}
]

- /home/ubuntu/monitor/watchers.json (list)
[
  {"wid":"w1","cid":"c1","session_token":"<token>","interval":60,"enabled":true,"created":1234567.0}
]

- ledger.log (append-only lines)
TS\tACTION\tsession_token\tcid\twid\tamount\tbalance_after\tnote

SQLite schema (recommended next step)
- sessions(id TEXT PRIMARY KEY, credits INTEGER, created REAL, last_used REAL, expires REAL, meta JSON)
- canonical_targets(cid TEXT PRIMARY KEY, fingerprint TEXT, url TEXT, probe_type TEXT, last_probe REAL, last_ok INTEGER)
- watchers(wid TEXT PRIMARY KEY, cid TEXT, session_token TEXT, interval INTEGER, enabled INTEGER, created REAL)
- ledger(id INTEGER PRIMARY KEY AUTOINCREMENT, ts REAL, action TEXT, session_token TEXT, cid TEXT, wid TEXT, amount INTEGER, balance INTEGER, note TEXT)

Migration notes
- Provide script to map existing monitor/db.json into canonical_targets + watchers with a default system session for legacy entries.
