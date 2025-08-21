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
        f.write(f"{ts}\t{action}\t{details}\n")

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
        import json
        cfg=json.loads(Path('/home/ubuntu/agent-repo/monitor/config.json').read_text())
        interval=max(t.get('interval',60), cfg.get('min_interval',60))
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
        # atomic DB write with lock
        try:
            import fcntl
            with open(DB,'r+') as df:
                try:
                    fcntl.flock(df, fcntl.LOCK_EX)
                    tmp=DB.with_suffix('.tmp')
                    tmp.write_text(json.dumps(data))
                    tmp.replace(DB)
                finally:
                    try:
                        fcntl.flock(df, fcntl.LOCK_UN)
                    except Exception:
                        pass
        except Exception:
            pass
        # attempt to consume credits via local API (always attempt)
        try:
            import requests
            resp=requests.post('http://127.0.0.1:8000/consume',json={'id':entry.get('id'),'cost':1},timeout=5)
            if resp.status_code==200:
                credits=resp.json().get('credits')
                log('CONSUME',f"id={entry.get('id')} cost=1 credits_left={credits}")
                # append to customer history
                from pathlib import Path
                custdir=Path('/home/ubuntu/agent-repo/monitor/customers')/entry.get('id')
                custdir.mkdir(parents=True,exist_ok=True)
                hist=custdir/'history.log'
                with open(hist,'a') as hf:
                    hf.write(f"{time.strftime('%Y-%m-%dT%H:%M:%S%z')}\tCHECK\tok={ok}\tcredits_left={credits}\n")
            else:
                try:
                    detail=resp.text
                except Exception:
                    detail='(no body)'
                log('CHECK_FAILED_CHARGE',f"id={entry.get('id')} status={resp.status_code} detail={detail}")
        except Exception as e:
            log('CHECK_CHARGE_ERR',str(e))
        
    time.sleep(5)
