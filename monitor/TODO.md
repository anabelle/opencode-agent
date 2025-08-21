# TODO (prioritized)

## Phase A - stabilize & sessionless MVP
- [x] Implement earnings ledger (earnings.log) and per-watcher receipts
- [x] Add customer history directories (customers/*)
- [ ] Implement sessions (session_token files) and migration script
- [ ] Update API to require/accept session_token and provide /session/topup
- [ ] Update UI to create session automatically after topup and redirect to /d/<token>
- [ ] Implement canonical targets and watcher model in scheduler

## Phase B - hardening
- [ ] Move persistence to SQLite
- [ ] Add rate-limiting and per-host probe throttling
- [ ] Admin dashboard: revoke sessions, export earnings
- [ ] Implement receipts download & session recovery

## Ops
- [ ] Automate daily backups and retention
- [ ] Add monitoring alerts for load/disk
