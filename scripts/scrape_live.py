"""Fetch the CURRENT program year, which the archive path cannot serve.

The year-prefixed path (/2026-2027/ClubReport.aspx) returns HTTP 500 until a
year closes, so the open year has to come from the UNPREFIXED path. That path
still honours ?month=, so we can pull the in-year trajectory as well as today.

Past months are cached permanently; the live month is refetched when stale.
"""
import os,sys,gzip,calendar,threading,queue,time,datetime,urllib.request

sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import common as C
_p = C.p

BASE="https://dashboards.toastmasters.org"
LIVE=_p("data","live"); os.makedirs(LIVE,exist_ok=True)
FRESH=6*3600          # refetch the open month if the cached copy is older
THREADS=8

def py_start(d):
    """Program years run Jul->Jun. Return the calendar year they start in."""
    return d.year if d.month>=7 else d.year-1

def months_so_far(start,today):
    """[(month, year, is_open_month)] for each month elapsed in the year."""
    out=[]
    for m in list(range(7,13))+list(range(1,7)):
        y=start if m>=7 else start+1
        if (y,m)>(today.year,today.month): break
        out.append((m,y,(y,m)==(today.year,today.month)))
    return out

def fetch(cid,m,y,is_open):
    key=os.path.join(LIVE,f"{cid}_{m:02d}.html.gz")
    if os.path.exists(key) and os.path.getsize(key)>500:
        if not is_open: return                      # closed month never changes
        if time.time()-os.path.getmtime(key)<FRESH: return
    # The open month wants the newest snapshot, so send no month/day at all.
    if is_open:
        url=f"{BASE}/ClubReport.aspx?id={cid}"
    else:
        last=calendar.monthrange(y,m)[1]
        url=f"{BASE}/ClubReport.aspx?id={cid}&month={m}&day={m}/{last}/{y}"
    for a in range(3):
        try:
            req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 (D21 DCP report)'})
            s=urllib.request.urlopen(req,timeout=45).read().decode('utf-8','replace')
            if 'csp-table' not in s and 'clubReportGoal' not in s: raise ValueError('not a club report')
            with gzip.open(key,'wt',encoding='utf-8') as f: f.write(s)
            return
        except Exception:
            if a==2: return
            time.sleep(1.5*(a+1))

def main():
    today=datetime.date.today()
    start=py_start(today); py=f"{start}-{start+1}"
    ms=months_so_far(start,today)
    clubs=[list(t) for t in C.load_clubs()]
    clubs=[n.zfill(8) for n,_ in clubs]
    jobs=[(c,m,y,o) for c in clubs for (m,y,o) in ms]
    print(f"program year {py}  clubs={len(clubs)}  months={len(ms)}  jobs={len(jobs)}",flush=True)
    q=queue.Queue()
    for j in jobs: q.put(j)
    done=[0]; lock=threading.Lock()
    def worker():
        while True:
            try: c,m,y,o=q.get_nowait()
            except queue.Empty: return
            fetch(c,m,y,o)
            with lock:
                done[0]+=1
                if done[0]%200==0: print(f"  {done[0]}/{len(jobs)}",flush=True)
    ts=[threading.Thread(target=worker,daemon=True) for _ in range(THREADS)]
    [t.start() for t in ts]; [t.join() for t in ts]
    print(f"DONE {done[0]}/{len(jobs)}  cache={LIVE}",flush=True)

if __name__=='__main__': main()
