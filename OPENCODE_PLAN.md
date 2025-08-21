Opencode MVP Plan

Summary:
- Objective: Make uptime-monitor MVP self-sustaining via Lightning micropayments (credit model).
- Current state: Local FastAPI API, checker daemon, simulated payments, backups to GitHub, admin key, per-customer history.

Short-term priorities (next session bootstrap):
1. Enable real Lightning invoices (LNbits preferred) and webhook verification.
2. Expose API publicly behind nginx + TLS with firewall and rate limits.
3. Add simple billing UI and landing page.
4. Start controlled marketing outreach (Nostr/Mastodon) after payments live.

Operational runbook (resume checklist):
- Ensure services: uvicorn (app) and checker running.
  - Start app: source /home/ubuntu/agent-repo/monitor/venv/bin/activate && python -m uvicorn app:app --host 127.0.0.1 --port 8000 &
  - Start checker: /home/ubuntu/agent-repo/monitor/admin.sh start
- Emergency pause: touch /home/ubuntu/agent-repo/monitor/EMERGENCY_PAUSE
- Admin key: /home/ubuntu/agent-repo/monitor/admin.key
- Backups: /home/ubuntu/recovery/, backups pushed to git@github.com:anabelle/opencode-backups.git

Security & safety reminders:
- Keep admin.key secret; store backups encrypted with passphrase.
- Do not enable auto-recharge without explicit approval.

Files of interest:
- /home/ubuntu/agent-repo/monitor/ (app.py, checker.py, config.json, admin.key)
- /home/ubuntu/opencode_actions.log
- /home/ubuntu/agents.md
- /home/ubuntu/agent-repo/scripts/backup_and_push.py

Next metrics to monitor:
- Daily top-ups (sats added)
- Active customers
- Average checks per customer
- VPS load and disk usage

Contact: operator (you) via the control session.
