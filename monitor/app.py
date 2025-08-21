from fastapi import FastAPI, HTTPException, BackgroundTasks
import uvicorn
import json, time, threading, os
from pathlib import Path

APPDIR=Path('/home/ubuntu/monitor')
LOG=Path('/home/ubuntu/opencode_actions.log')
DB=APPDIR/'db.json'
if not DB.exists(): DB.write_text('[]')
app=FastAPI()

def log(action, details=''):
    ts=time.strftime('%Y-%m-%dT%H:%M:%S%z')
    with open(LOG,'a') as f:
        f.write(f"{ts}	{action}	{details}
")

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

if __name__=='__main__':
    uvicorn.run(app,host='127.0.0.1',port=8000)
