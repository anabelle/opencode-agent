import time, json
from pathlib import Path
BASE=Path(__file__).parent
RESULTS=BASE/'results'
ANALYTICS=BASE/'analytics'

def tail_lines(path, n=100):
    if not path.exists():
        return []
    with path.open() as f:
        lines=f.readlines()[-n:]
    return [json.loads(l) for l in lines]

def reports_for_cid(cid, limit=100):
    p=RESULTS/f"{cid}.log"
    return tail_lines(p, n=limit)

def timeseries_for_wid(token,wid, limit=100):
    p=BASE/f"customers/{token}/watchers/{wid}.log"
    return tail_lines(p, n=limit)

def analytics_for_cid(cid):
    p=ANALYTICS/f"{cid}.json"
    if p.exists():
        return json.loads(p.read_text())
    return {}
