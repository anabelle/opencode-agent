from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, PlainTextResponse
import uvicorn, time, json
from pathlib import Path
from monitor import db
import uuid

APPDIR=Path('/home/ubuntu/agent-repo/monitor')
LOG=Path('/home/ubuntu/opencode_actions.log')
UI_DIR=APPDIR/'ui'

app=FastAPI()

def log(action, details=''):
    ts=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
    with open(LOG,'a') as f:
        f.write(f"{ts}\t{action}\t{details}\n")

def check_admin_key(headers):
    kfile=Path('/home/ubuntu/agent-repo/monitor/admin.key')
    if not kfile.exists(): return False
    expected=kfile.read_text().strip()
    return headers.get('x-admin-key')==expected

# simple canonicalization: lowercase, strip trailing slash
from urllib.parse import urlparse, urlunparse

def normalize_url(u):
    p=urlparse(u)
    scheme=p.scheme or 'http'
    netloc=p.netloc.lower()
    path=p.path.rstrip('/')
    return urlunparse((scheme, netloc, path, '', '', ''))

@app.post('/init')
async def init():
    db.init_db()
    return {'status':'ok'}

@app.post('/topup')
async def topup(data: dict):
    # simulated topup: creates session if token not provided
    sats=int(data.get('sats',0))
    if sats<=0:
        raise HTTPException(status_code=400, detail='sats must be >0')
    token=data.get('token')
    ts=time.time()
    with db.get_conn() as conn:
        c=conn.cursor()
        if not token:
            token=str(uuid.uuid4())
            c.execute('insert into sessions(token,credits,created,last_used) values(?,?,?,?)', (token, sats, ts, ts))
            balance=sats
            action='CREATE_SESSION_TOPUP'
        else:
            cur=c.execute('select credits from sessions where token=?', (token,)).fetchone()
            if not cur:
                raise HTTPException(status_code=404, detail='session not found')
            balance=cur['credits']+sats
            c.execute('update sessions set credits=?, last_used=? where token=?', (balance, ts, token))
            action='TOPUP'
        c.execute('insert into ledger(ts,action,token,amount,balance,note) values(?,?,?,?,?,?)', (ts, action, token, sats, balance, None))
        conn.commit()
    log('TOPUP', f"token={token} sats={sats} balance={balance}")
    # return a small HTML page that redirects to dashboard for friendliness
    html = f"<html><head><meta http-equiv='refresh' content='0; url=/d/{token}'></head><body>Topup successful. Redirecting to dashboard... If not redirected, <a href='/d/{token}'>click here</a>.</body></html>"
    return HTMLResponse(content=html, status_code=200)

@app.post('/register')
async def register(data: dict):
    # expects {"token":..., "url":..., "interval":60}
    token=data.get('token')
    url=data.get('url')
    interval=int(data.get('interval',60))
    if not token or not url:
        raise HTTPException(status_code=400, detail='missing token or url')
    norm=normalize_url(url)
    cid=str(uuid.uuid5(uuid.NAMESPACE_URL, norm))
    ts=time.time()
    with db.get_conn() as conn:
        c=conn.cursor()
        # ensure session exists
        if not c.execute('select 1 from sessions where token=?',(token,)).fetchone():
            raise HTTPException(status_code=404, detail='session not found')
        # ensure canonical target exists
        if not c.execute('select 1 from canonical_targets where cid=?',(cid,)).fetchone():
            c.execute('insert into canonical_targets(cid,url,fingerprint,probe_type,last_probe,last_ok,next_run) values(?,?,?,?,?,?,?)', (cid, norm, None, 'http', None, 0, ts))
        # create watcher
        wid=str(int(time.time()*1000))
        c.execute('insert into watchers(wid,cid,token,interval,enabled,created) values(?,?,?,?,?,?)', (wid, cid, token, interval, 1, ts))
        conn.commit()
    log('REGISTER', f"token={token} wid={wid} cid={cid} url={norm}")
    return {'wid':wid, 'cid':cid, 'url':norm}

@app.get('/d/{token}')
async def dashboard(token: str):
    with db.get_conn() as conn:
        c=conn.cursor()
        session=c.execute('select token,credits,created,last_used from sessions where token=?',(token,)).fetchone()
        if not session:
            raise HTTPException(status_code=404, detail='session not found')
        watchers=c.execute('select w.wid,w.interval,w.enabled,w.created, t.url from watchers w join canonical_targets t on w.cid=t.cid where w.token=?',(token,)).fetchall()
        wlist=[dict(w) for w in watchers]
        return {'session':dict(session), 'watchers':wlist}

@app.get('/', response_class=HTMLResponse)
async def ui_index():
    idx=UI_DIR/'index.html'
    if idx.exists():
        return HTMLResponse(idx.read_text())
    return HTMLResponse('<h1>Opencode Monitor</h1>')

@app.get('/targets')
async def list_targets():
    with db.get_conn() as conn:
        c=conn.cursor()
        rows=c.execute('select cid,url,last_probe,last_ok,next_run from canonical_targets').fetchall()
        return [dict(r) for r in rows]

import monitor.reports as reports

@app.get('/reports/cid/{cid}')
async def report_cid(cid: str, limit: int = 100):
    return reports.reports_for_cid(cid)

@app.get('/reports/wid/{token}/{wid}')
async def report_wid(token: str, wid: str, limit: int = 100):
    return reports.timeseries_for_wid(token, wid, limit=limit)

@app.post('/consume')
async def consume(data: dict):
    wid=data.get('wid')
    cost=int(data.get('cost',1))
    ts=time.time()
    if not wid:
        raise HTTPException(status_code=400, detail='missing wid')
    with db.get_conn() as conn:
        c=conn.cursor()
        row=c.execute('select token from watchers where wid=?',(wid,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail='watcher not found')
        token=row['token']
        cur=c.execute('select credits from sessions where token=?',(token,)).fetchone()
        if cur['credits']>=cost:
            newbal=cur['credits']-cost
            c.execute('update sessions set credits=?, last_used=? where token=?',(newbal, ts, token))
            c.execute('insert into ledger(ts,action,token,wid,amount,balance) values(?,?,?,?,?,?)',(ts,'CONSUME',token,wid,cost,newbal))
            conn.commit()
            log('CONSUME',f"wid={wid} token={token} cost={cost} credits_left={newbal}")
            return {'status':'ok','credits':newbal}
        else:
            c.execute('insert into ledger(ts,action,token,wid,amount,balance,note) values(?,?,?,?,?,?,?)',(ts,'CHECK_FAILED_CHARGE',token,wid,cost,cur['credits'],'insufficient funds'))
            conn.commit()
            raise HTTPException(status_code=402, detail='insufficient funds')

if __name__=='__main__':
    db.init_db()
    uvicorn.run('monitor.app:app',host='127.0.0.1',port=8000,log_level='info')
