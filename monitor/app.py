from fastapi import FastAPI, HTTPException, BackgroundTasks
import uvicorn
import json, time, threading, os
from pathlib import Path
from fastapi import FastAPI, HTTPException

APPDIR=Path('/home/ubuntu/monitor')
LOG=Path('/home/ubuntu/opencode_actions.log')
DB=APPDIR/'db.json'
if not DB.exists(): DB.write_text('[]')
app=FastAPI()

def log(action, details=''):
    ts=time.strftime('%Y-%m-%dT%H:%M:%S%z')
    with open(LOG,'a') as f:
        f.write(f"{ts}\t{action}\t{details}\n")

def check_admin_key(headers):
    from pathlib import Path
    kfile=Path('/home/ubuntu/agent-repo/monitor/admin.key')
    if not kfile.exists(): return False
    expected=kfile.read_text().strip()
    return headers.get('x-admin-key')==expected

from fastapi import Request

@app.post('/register')
async def register(request: Request, headers: dict = None):
    try:
        body = await request.json()
    except Exception:
        body = {}

    # allow registration without admin key for MVP
    # body may be either {'target':{...}} or {'url':'...','interval':N}
    if headers is None:
        headers = {}
    target=body.get('target')
    if not target:
        # accept flat format
        url=body.get('url')
        interval=body.get('interval',60)
        if not url:
            raise HTTPException(status_code=400,detail='missing target url')
        target={'url':url,'interval':interval}
    # basic validation
    if 'url' not in target:
        raise HTTPException(status_code=400,detail='missing target.url')

    data=json.loads(DB.read_text())
    # deduplicate: if same target url+interval exists, return existing id
    for entry in data:
        t=entry.get('target',{})
        if t.get('url')==target.get('url') and int(t.get('interval',0))==int(target.get('interval',0)):
            log('REGISTER_DUP',f"returned existing id={entry.get('id')} target={target}")
            return {'id':entry.get('id'),'duplicate':True}
    entry={'id':str(int(time.time()*1000)),'target':target,'credits':0,'created':time.time()}
    data.append(entry)
    DB.write_text(json.dumps(data))
    log('REGISTER',str(entry))
    return {'id':entry['id']}

@app.get('/targets')
async def list_targets():
    return json.loads(DB.read_text())

# UI routes
from fastapi.responses import HTMLResponse, PlainTextResponse
UI_DIR=Path('/home/ubuntu/agent-repo/monitor/ui')

@app.get('/', response_class=HTMLResponse)
async def ui_index():
    idx=UI_DIR/'index.html'
    if idx.exists():
        return HTMLResponse(idx.read_text())
    return HTMLResponse('<h1>Opencode Monitor</h1>')

# admin earnings page (requires x-admin-key header)
@app.get('/admin/earnings')
async def admin_earnings(request: Request):
    if not check_admin_key(request.headers):
        return PlainTextResponse('unauthorized',status_code=403)
    earn=Path('/home/ubuntu/agent-repo/monitor/earnings.log')
    if not earn.exists():
        return PlainTextResponse('no earnings yet')
    text=earn.read_text()
    # compute total
    total=0
    for line in text.splitlines():
        parts=line.split('\t')
        for p in parts:
            if p.startswith('cost='):
                try:
                    total+=int(p.split('=')[1])
                except Exception:
                    pass
    return PlainTextResponse(f"total earnings sats={total}\n\n"+text)

@app.post('/topup')
async def topup(data: dict):
    # simulated invoice: credit top-up immediately for MVP
    db=json.loads(DB.read_text())
    cid=data.get('id')
    amt=int(data.get('sats',0))
    if not cid or amt<=0:
        raise HTTPException(status_code=400,detail='bad request')
    for entry in db:
        if entry['id']==cid:
            entry['credits']=entry.get('credits',0)+amt
            DB.write_text(json.dumps(db))
            log('TOPUP',f"id={cid} sats={amt} new_credits={entry['credits']}")
            return {'status':'ok','credits':entry['credits']}
    raise HTTPException(status_code=404,detail='not found')

import fcntl

@app.post('/consume')
async def consume(request: Request):
    # consume credits for a check; called by checker
    try:
        data = await request.json()
    except Exception:
        data = {}
    cid=data.get('id')
    cost=int(data.get('cost',1))
    # file locking to prevent concurrent writes
    earn_path=Path('/home/ubuntu/agent-repo/monitor/earnings.log')
    with open(DB, 'r+') as f:
        try:
            fcntl.flock(f, fcntl.LOCK_EX)
            raw=f.read()
            db=json.loads(raw) if raw else []
            for entry in db:
                if entry['id']==cid:
                    if entry.get('credits',0)>=cost:
                        entry['credits']=entry.get('credits',0)-cost
                        f.seek(0); f.truncate(0); f.write(json.dumps(db))
                        f.flush()
                        # record earnings
                        with open(earn_path,'a') as ef:
                            ef.write(f"{time.strftime('%Y-%m-%dT%H:%M:%S%z')}\tEARN\tid={cid}\tcost={cost}\tcredits_left={entry['credits']}\n")
                        log('CONSUME',f"id={cid} cost={cost} credits_left={entry['credits']}")
                        return {'status':'ok','credits':entry['credits']}
                    else:
                        raise HTTPException(status_code=402,detail='insufficient funds')
            raise HTTPException(status_code=404,detail='not found')
        finally:
            try:
                fcntl.flock(f, fcntl.LOCK_UN)
            except Exception:
                pass


if __name__=='__main__':
    uvicorn.run(app,host='127.0.0.1',port=8000)
