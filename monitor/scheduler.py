import asyncio
import aiohttp
import time, json
from pathlib import Path
from monitor import db

BASE=Path(__file__).parent
RESULTS=BASE/'results'
ANALYTICS=BASE/'analytics'
PAUSE=BASE/'EMERGENCY_PAUSE'
RESULTS.mkdir(exist_ok=True)
ANALYTICS.mkdir(exist_ok=True)

CONCURRENCY=4
PROBE_TIMEOUT=10
MIN_INTERVAL=30

async def probe_target(session, cid, url):
    ts=time.time()
    try:
        start=time.time()
        async with session.get(url, timeout=PROBE_TIMEOUT) as resp:
            body=await resp.read()
            latency=(time.time()-start)*1000
            rec={
                'ts':ts,'cid':cid,'status':'ok','http_status':resp.status,'latency_ms':latency,'size':len(body)
            }
    except Exception as e:
        rec={'ts':ts,'cid':cid,'status':'error','error':str(e)}
    # append to results log
    p=RESULTS/f"{cid}.log"
    with p.open('a') as f:
        f.write(json.dumps(rec)+"\n")
    return rec

async def handle_canonical(cid, url, simulate=False):
    async with aiohttp.ClientSession() as session:
        rec=await probe_target(session,cid,url)
    # update DB
    now=time.time()
    with db.get_conn() as conn:
        c=conn.cursor()
        last_ok=1 if rec.get('status')=='ok' else 0
        c.execute('update canonical_targets set last_probe=?, last_ok=?, next_run=? where cid=?',(now,last_ok, now+MIN_INTERVAL, cid))
        # get watchers
        rows=c.execute('select wid,token,interval from watchers where cid=? and enabled=1',(cid,)).fetchall()
        for w in rows:
            wid=w['wid']
            token=w['token']
            # write per-watcher history
            cust_dir=BASE/f"customers/{token}"/watchers
            cust_dir.mkdir(parents=True, exist_ok=True)
            hist=cust_dir/f"{wid}.log"
            entry={'ts':now,'wid':wid,'cid':cid,'probe':rec}
            with hist.open('a') as hf:
                hf.write(json.dumps(entry)+"\n")
            # attempt consume
            if simulate:
                continue
            cur=c.execute('select credits from sessions where token=?',(token,)).fetchone()
            cost=1
            if cur and cur['credits']>=cost:
                newbal=cur['credits']-cost
                c.execute('update sessions set credits=?, last_used=? where token=?',(newbal, now, token))
                c.execute('insert into ledger(ts,action,token,wid,amount,balance) values(?,?,?,?,?,?)',(now,'CONSUME',token,wid,cost,newbal))
            else:
                c.execute('insert into ledger(ts,action,token,wid,amount,balance,note) values(?,?,?,?,?,?,?)',(now,'CHECK_FAILED_CHARGE',token,wid,cost,cur['credits'] if cur else 0,'insufficient funds'))
        conn.commit()
    # update analytics (simple rolling counters)
    a_file=ANALYTICS/f"{cid}.json"
    agg={'checks_total':0,'checks_ok':0,'avg_latency_ms':None}
    if a_file.exists():
        try:
            agg=json.loads(a_file.read_text())
        except Exception:
            agg={'checks_total':0,'checks_ok':0,'avg_latency_ms':None}
    agg['checks_total']=agg.get('checks_total',0)+1
    if rec.get('status')=='ok':
        agg['checks_ok']=agg.get('checks_ok',0)+1
        lat=rec.get('latency_ms',0)
        if agg.get('avg_latency_ms') is None:
            agg['avg_latency_ms']=lat
        else:
            agg['avg_latency_ms']=(agg['avg_latency_ms']*(agg['checks_ok']-1)+lat)/agg['checks_ok']
    a_file.write_text(json.dumps(agg))

async def scheduler_loop(simulate=False):
    sem=asyncio.Semaphore(CONCURRENCY)
    while True:
        if PAUSE.exists():
            await asyncio.sleep(5)
            continue
        # load due canonical targets
        now=time.time()
        tasks=[]
        with db.get_conn() as conn:
            c=conn.cursor()
            rows=c.execute('select cid,url,next_run from canonical_targets where next_run is null or next_run<=? order by next_run asc',(now,)).fetchall()
            for r in rows:
                cid=r['cid']; url=r['url']
                await sem.acquire()
                t=asyncio.create_task(run_with_sem(sem, cid, url, simulate))
                tasks.append(t)
        if tasks:
            await asyncio.gather(*tasks)
        await asyncio.sleep(1)

async def run_with_sem(sem,cid,url,simulate):
    try:
        await handle_canonical(cid,url,simulate=simulate)
    finally:
        sem.release()

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument('--simulate',action='store_true')
    args=p.parse_args()
    db.init_db()
    asyncio.run(scheduler_loop(simulate=args.simulate))
