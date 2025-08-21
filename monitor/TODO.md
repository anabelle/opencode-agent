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

## Testing
- [x] Set up testing framework (pytest, coverage) - 74% overall coverage achieved
- [x] Add unit tests for core components:
  - [x] Database operations (db.py) - 100% coverage
  - [x] API endpoints (app.py) - 97% coverage
  - [ ] Checker logic (checker.py) - 0% coverage (tests created but need debugging)
  - [x] Report generation (reports.py) - 100% coverage
- [x] Add integration tests for API endpoints - 21 comprehensive tests added
- [x] Add database migration and schema tests - Full schema validation tests
- [x] Add end-to-end tests for watcher registration and monitoring - Complete workflow tests
- [ ] Set up CI/CD pipeline for automated testing
- [ ] Add performance tests for monitoring under load
- [ ] Debug and fix checker.py tests (currently hanging due to file system dependencies)

## Ops
- [x] Automate daily backups and retention (implemented via cron)
- [x] Add monitoring alerts for load/disk (disk_monitor.sh, hourly checks)
- [ ] Add comprehensive system health monitoring
