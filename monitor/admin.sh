#!/usr/bin/env bash
set -e
case "$1" in
 start) pkill -f checker.py || true; nohup python3 /home/ubuntu/monitor/checker.py >/home/ubuntu/monitor/checker.log 2>&1 & echo started;;
 stop) pkill -f checker.py || true; echo stopped;;
 status) pgrep -af checker.py || echo not running;;
 backup) tar czf /home/ubuntu/recovery/monitor-$(date +%F).tar.gz -C /home/ubuntu monitor && echo backed;;
 *) echo "usage: $0 {start|stop|status|backup}";;
esac