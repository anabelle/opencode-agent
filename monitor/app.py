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

@app.post('/register')
async def register(target: dict):
    data=json.loads(DB.read_text())
    entry={'id':str(int(time.time()*1000)),'target':target,'credits':0,'created':time.time()}
    data.append(entry)
    DB.write_text(json.dumps(data))
    log('REGISTER',str(entry))
    return {'id':entry['id']}

@app.get('/targets')
async def list_targets():
    return json.loads(DB.read_text())

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

@app.post('/consume')
async def consume(data: dict):
    # consume credits for a check; called by checker
    db=json.loads(DB.read_text())
    cid=data.get('id')
    cost=int(data.get('cost',1))
    for entry in db:
        if entry['id']==cid:
            if entry.get('credits',0)>=cost:
                entry['credits']-=cost
                DB.write_text(json.dumps(db))
                log('CONSUME',f"id={cid} cost={cost} credits_left={entry['credits']}")
                return {'status':'ok','credits':entry['credits']}
            else:
                raise HTTPException(status_code=402,detail='insufficient funds')
    raise HTTPException(status_code=404,detail='not found')

if __name__=='__main__':
    uvicorn.run(app,host='127.0.0.1',port=8000)
