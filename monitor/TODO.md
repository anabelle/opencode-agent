# TODO (prioritized)

## Phase A - stabilize & sessionless MVP
- [x] Implement earnings ledger (earnings.log) and per-watcher receipts
- [x] Add customer history directories (customers/*)
- [x] Implement sessions (session_token files) and migration script
- [x] Update API to require/accept session_token and provide /session/topup
- [x] Update UI to create session automatically after topup and redirect to /d/<token>
- [x] Implement canonical targets and watcher model in scheduler

## Phase B - hardening
- [ ] Move persistence to SQLite
- [ ] Add rate-limiting and per-host probe throttling
- [ ] Admin dashboard: revoke sessions, export earnings
- [ ] Implement receipts download & session recovery

## Ops
- [ ] Automate daily backups and retention
- [ ] Add monitoring alerts for load/disk
