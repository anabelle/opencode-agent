BOOTSTRAP - Start a new session quickly

1. Start services
   - Start checker:
     /home/ubuntu/agent-repo/monitor/admin.sh start
   - Ensure uvicorn FastAPI is running (systemd user):
     systemctl --user start opencode-monitor.service

2. Create a session (simulate topup)
   - Use the UI: visit http://vm-522.lnvps.cloud/ and click start/topup (simulated)
   - Or use API to create and topup:
     curl -X POST http://127.0.0.1:8000/register -H 'Content-Type: application/json' -d '{"target":{"url":"https://example.com","interval":60}}'
     curl -X POST http://127.0.0.1:8000/topup -H 'Content-Type: application/json' -d '{"id":"<id>","sats":200}'

3. Save your session token
   - Copy the returned id and store locally; this is your session identifier for the dashboard.

4. Access dashboard
   - Visit http://vm-522.lnvps.cloud/ and use the token to manage targets.

Notes
- For full sessionless flow, use the session token returned after payment/topup. Save and backup it.
- Admin key located at /home/ubuntu/agent-repo/monitor/admin.key (permissions 600). Use header x-admin-key for admin endpoints.
