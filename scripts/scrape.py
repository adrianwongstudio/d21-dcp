import os,sys,gzip,calendar,threading,queue,time,urllib.request
import os as _os
_ROOT=_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
def _p(*a): return _os.path.join(_ROOT,*a)

BASE="https://dashboards.toastmasters.org"
CACHE=_p("data","cache"); os.makedirs(CACHE,exist_ok=True)

def months():
    out=[]
    for start in [2021,2022,2023,2024,2025]:
        py=f"{start}-{start+1}"
        for m in range(7,13): out.append((py,m,start))
        for m in range(1,7):  out.append((py,m,start+1))
    return out

def lastday(m,y): return f"{m}/{calendar.monthrange(y,m)[1]}/{y}"

def fetch(py,m,y,cid):
    key=os.path.join(CACHE,f"{cid}_{py}_{m:02d}.html.gz")
    if os.path.exists(key) and os.path.getsize(key)>500: return
    url=f"{BASE}/{py}/ClubReport.aspx?id={cid}&month={m}&day={lastday(m,y)}"
    for a in range(3):
        try:
            req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 (D21 DCP report)'})
            s=urllib.request.urlopen(req,timeout=45).read().decode('utf-8','replace')
            with gzip.open(key,'wt',encoding='utf-8') as f: f.write(s)
            return
        except Exception:
            if a==2: return
            time.sleep(1.5*(a+1))

def main():
    clubs=[l.rstrip('\n').split('\t') for l in open(_p('scripts','clubs.tsv')) if l.strip()]
    clubs=[(n.zfill(8),nm) for n,nm in clubs]
    MS=months()
    jobs=[(cid,py,m,y) for cid,_ in clubs for (py,m,y) in MS]
    print(f"clubs={len(clubs)} months={len(MS)} jobs={len(jobs)}",flush=True)
    q=queue.Queue()
    for j in jobs: q.put(j)
    done=[0]; lock=threading.Lock()
    def worker():
        while True:
            try: cid,py,m,y=q.get_nowait()
            except queue.Empty: return
            fetch(py,m,y,cid)
            with lock:
                done[0]+=1
                if done[0]%500==0: print(f"  {done[0]}/{len(jobs)}",flush=True)
    ts=[threading.Thread(target=worker,daemon=True) for _ in range(8)]
    [t.start() for t in ts]; [t.join() for t in ts]
    print(f"DONE {done[0]}/{len(jobs)}",flush=True)

if __name__=='__main__': main()
