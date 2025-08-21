BOOTSTRAP - Start a new session quickly

## System Status
✅ **Services**: Both FastAPI and scheduler are configured to start automatically at boot
✅ **Log Management**: Automatic rotation, compression, and disk monitoring active
✅ **Health Monitoring**: Daily health checks and automated backups

## Quick Start

1. **Check services** (should be running automatically):
    ```bash
    systemctl --user status opencode-monitor.service opencode-scheduler.service
    ```

2. **Create a session** (simulate topup):
    - Use the UI: visit http://vm-522.lnvps.cloud/ and click start/topup (simulated)
    - Or use API to create and topup:
      ```bash
      curl -X POST http://127.0.0.1:8000/register -H 'Content-Type: application/json' -d '{"target":{"url":"https://example.com","interval":60}}'
      curl -X POST http://127.0.0.1:8000/topup -H 'Content-Type: application/json' -d '{"id":"<id>","sats":200}'
      ```

3. **Save your session token**
    - Copy the returned id and store locally; this is your session identifier for the dashboard.

4. **Access dashboard**
    - Visit http://vm-522.lnvps.cloud/ and use the token to manage targets.

## System Management

### Services
- **FastAPI Server**: `systemctl --user start opencode-monitor.service`
- **Scheduler**: `systemctl --user start opencode-scheduler.service`
- **Status**: `systemctl --user status opencode-monitor.service opencode-scheduler.service`

### Log Management
- **Automatic rotation**: Daily at 2 AM, 7-day retention, 10MB max per file
- **Disk monitoring**: Hourly checks, alerts at 85% usage
- **Emergency cleanup**: Daily at 3:30 AM when disk >90%

### Monitoring
- **Health checks**: Daily at 3 AM
- **Backups**: Daily at 4 AM to `/home/ubuntu/recovery/`
- **Disk alerts**: Logged to `opencode_actions.log`

## Notes
- For full sessionless flow, use the session token returned after payment/topup. Save and backup it.
- Admin key located at `/home/ubuntu/agent-repo/monitor/admin.key` (permissions 600). Use header x-admin-key for admin endpoints.
- System is fully automated with log rotation, disk monitoring, and emergency cleanup.
