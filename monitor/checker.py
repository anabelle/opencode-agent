#!/usr/bin/env python3
import json
import subprocess
import sys
import time
from pathlib import Path

sys.path.append("/home/ubuntu/agent-repo/monitor")
import db

LOG = Path("/home/ubuntu/opencode_actions.log")
EMER = Path("/home/ubuntu/monitor") / "EMERGENCY_PAUSE"


def log(action, details=""):
    ts = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    with open(LOG, "a") as f:
        f.write(f"{ts}\t{action}\t{details}\n")


while True:
    if EMER.exists():
        log("CHECKER_PAUSED", "Emergency pause present")
        time.sleep(30)
        continue

    # Sleep at the beginning of each cycle to prevent excessive CPU usage
    time.sleep(5)
    try:
        with db.get_conn() as conn:
            c = conn.cursor()
            # Get watchers with their target information
            data = c.execute(
                """
                SELECT w.wid, w.interval, w.enabled, t.url, t.probe_type
                FROM watchers w
                JOIN canonical_targets t ON w.cid = t.cid
                WHERE w.enabled = 1
            """
            ).fetchall()
            data = [dict(row) for row in data]
    except Exception as e:
        log("CHECKER_DB_ERROR", str(e))
        data = []
    for entry in data:

        url = entry.get("url")
        probe_type = entry.get("probe_type", "http")
        import json

        cfg = json.loads(
            Path("/home/ubuntu/agent-repo/monitor/config.json").read_text()
        )
        interval = max(entry.get("interval", 60), cfg.get("min_interval", 60))

        # Get the original interval from database for timing calculations
        original_interval = entry.get("interval", 60)

        # Check if we should run this check
        # Use the watcher's specific interval instead of shared canonical target timing
        with db.get_conn() as conn:
            c = conn.cursor()
            # Get the last probe time for this specific watcher
            row = c.execute(
                "SELECT last_probe FROM watchers WHERE wid = ?", (entry.get("wid"),)
            ).fetchone()
            last_probe = row["last_probe"] if row else 0
            if time.time() < (last_probe + original_interval):
                continue

        # simple HTTP/port probe
        ok = False
        latency_ms = 0
        size = 0
        if url and probe_type == "http":
            try:
                import time

                # Use curl to get timing info in a clean format
                r = subprocess.run(
                    [
                        "curl",
                        "-sS",
                        "--max-time",
                        "10",
                        "-o",
                        "/dev/null",
                        "-w",
                        "%{time_total}:%{size_download}",
                        url,
                    ],
                    capture_output=True,
                    text=True,
                )
                ok = r.returncode == 0
                if ok and r.stdout:
                    # Parse curl output: "time_total:size_download"
                    parts = r.stdout.strip().split(":")
                    if len(parts) == 2:
                        try:
                            latency_ms = (
                                float(parts[0]) * 1000
                            )  # Convert seconds to milliseconds
                            size = int(parts[1])  # Response size in bytes
                        except ValueError:
                            pass
            except Exception:
                ok = False
        elif probe_type == "port" and "host" in entry and "port" in entry:
            import socket

            s = socket.socket()
            s.settimeout(5)
            try:
                s.connect((entry["host"], int(entry["port"])))
                ok = True
            except Exception:
                ok = False
            finally:
                s.close()

        # Update the database with results
        try:
            with db.get_conn() as conn:
                c = conn.cursor()
                now = time.time()
                # Only update the watcher's own last_probe time - don't affect other watchers
                c.execute(
                    "UPDATE watchers SET last_probe = ? WHERE wid = ?",
                    (now, entry.get("wid")),
                )
                conn.commit()
        except Exception as e:
            log("CHECKER_UPDATE_ERROR", str(e))
        # attempt to consume credits via local API (always attempt)
        try:
            import requests

            resp = requests.post(
                "http://127.0.0.1:8000/consume",
                json={"wid": entry.get("wid"), "cost": 1},
                timeout=5,
            )
            if resp.status_code == 200:
                credits = resp.json().get("credits")
                log("CONSUME", f"wid={entry.get('wid')} cost=1 credits_left={credits}")
                # append to customer history
                from pathlib import Path

                wid = entry.get("wid")
                if wid:
                    # Get the token for this watcher to construct the correct path
                    with db.get_conn() as conn:
                        c = conn.cursor()
                        token_row = c.execute(
                            "SELECT token FROM watchers WHERE wid = ?", (wid,)
                        ).fetchone()
                        if token_row:
                            token = token_row["token"]
                            custdir = (
                                Path("/home/ubuntu/agent-repo/monitor/customers")
                                / token
                                / "watchers"
                            )
                            custdir.mkdir(parents=True, exist_ok=True)
                            hist = custdir / f"{wid}.log"
                            # Write in JSON format for consistency with other history files
                            import json

                            history_entry = {
                                "ts": time.time(),
                                "wid": wid,
                                "cid": entry.get("cid", ""),
                                "probe": {
                                    "ts": time.time(),
                                    "status": "ok" if ok else "fail",
                                    "http_status": 200 if ok else 0,
                                    "latency_ms": latency_ms,
                                    "size": size,
                                },
                            }
                            with open(hist, "a") as hf:
                                hf.write(json.dumps(history_entry) + "\n")
            else:
                try:
                    detail = resp.text
                except Exception:
                    detail = "(no body)"
                log(
                    "CHECK_FAILED_CHARGE",
                    f"wid={entry.get('wid')} status={resp.status_code} detail={detail}",
                )
        except Exception as e:
            log("CHECK_CHARGE_ERR", str(e))
