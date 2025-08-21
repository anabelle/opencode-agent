#!/usr/bin/env python3
import time, json, subprocess
from pathlib import Path
APP=Path('/home/ubuntu/monitor')
DB=APP/'db.json'
LOG=Path('/home/ubuntu/opencode_actions.log')
EMER=APP/'EMERGENCY_PAUSE'

def log(action,details=''):
    ts=time.strftime('%Y-%m-%dT%H:%M:%S%z')
    with open(LOG,'a') as f:
        f.write(f"{ts}	{action}	{details}
")

while True:
    if EMER.exists():
        log('CHECKER_PAUSED','Emergency pause present')
        time.sleep(30)
        continue
    try:
        data=json.loads(DB.read_text())
    except Exception:
        data=[]
    for entry in data:
        t=entry.get('target')
        if not t: continue
        url=t.get('url')
        port=t.get('port')
        interval=t.get('interval',60)
        last=entry.get('last_check',0)
        if time.time()-last<interval: continue
        # simple HTTP/port probe
        ok=False
        if url:
            try:
                r=subprocess.run(['curl','-sSf','--max-time','10',url],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
                ok=(r.returncode==0)
            except Exception:
                ok=False
        elif port and 'host' in t:
            import socket
            s=socket.socket(); s.settimeout(5)
            try:
                s.connect((t['host'],int(port)))
                ok=True
            except Exception:
                ok=False
            finally:
                s.close()
        entry['last_check']=time.time()
        entry['last_ok']=ok
        log('CHECK',f"id={entry.get('id')} ok={ok} target={t}")
    try:
        open(DB,'w').write(json.dumps(data))
    except Exception:
        pass
    time.sleep(5)
