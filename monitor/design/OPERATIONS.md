# OPERATIONS

Backups
- Daily tarball of /home/ubuntu/monitor and /home/ubuntu/agent-repo/monitor to /home/ubuntu/recovery
- Store one-week rotation locally

Certs
- Certbot installed; renewal timer enabled; deploy hook reloads nginx

Healthchecks
- healthcheck.sh exists; schedule cron or systemd timer for periodic checks (disk, load, process running)

Emergency procedures
- Create /home/ubuntu/agent-repo/monitor/EMERGENCY_PAUSE to pause checker
- Admin key at /home/ubuntu/agent-repo/monitor/admin.key controls admin endpoints

Logging
- /home/ubuntu/opencode_actions.log: master action log
- /home/ubuntu/agent-repo/monitor/earnings.log: ledger of consumes
- Per-session receipts and per-watcher history files
