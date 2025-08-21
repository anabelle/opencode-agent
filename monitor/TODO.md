# TODO (prioritized)

## System Status (2025-08-21)
- **Services**: FastAPI server (port 8000) and scheduler both active
- **Watchers**: 12 enabled watchers, 21 active sessions, 238013 total credits
- **Database**: SQLite with enhanced schema (last_probe column added)
- **History**: Token-based JSON logging system implemented
- **Timing**: Per-watcher timing prevents URL-based conflicts
- **Health**: Load 1.00, Disk 9%, all monitoring systems active

---

## Phase A - stabilize & sessionless MVP
- [x] Implement earnings ledger (earnings.log) and per-watcher receipts
- [x] Add customer history directories (customers/*)
- [x] Implement sessions (session_token files) and migration script
- [x] Update API to require/accept session_token and provide /session/topup
- [x] Update UI to create session automatically after topup and redirect to /d/<token>
- [x] Implement canonical targets and watcher model in scheduler

## Phase B - hardening
- [x] Move persistence to SQLite (2025-08-21: Migrated checker from JSON to SQLite database)
- [ ] Add rate-limiting and per-host probe throttling
- [ ] Admin dashboard: revoke sessions, export earnings
- [ ] Implement receipts download & session recovery

## Recent Fixes (2025-08-21)
- [x] Fix timing conflicts between watchers with different intervals
- [x] Resolve "missing wid" errors in checker
- [x] Implement per-watcher timing using last_probe column
- [x] Fix history logging to use token-based paths with JSON format
- [x] Add last_probe column to watchers table for independent timing
- [x] Resolve all watcher functionality issues (credits, history, timing)

## Ops
- [x] Automate daily backups and retention (implemented via cron)
- [x] Add monitoring alerts for load/disk (disk_monitor.sh, hourly checks)
- [ ] Add comprehensive system health monitoring
