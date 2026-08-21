import os as _os, json, collections
_ROOT=_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
def _p(*a): return _os.path.join(_ROOT,*a)

PYS=["2021-2022","2022-2023","2023-2024","2024-2025","2025-2026"]
MORD=[7,8,9,10,11,12,1,2,3,4,5,6]
GOALS=["Level 1 awards","Level 2 awards","More Level 2 awards","Level 3 awards",
"Level 4, Path Completion, or DTM award","One more Level 4, Path Completion, or DTM award",
"New members","More new members","Club officer roles trained June-August",
"Club officer roles trained November-February","Membership-renewal dues on time",
"Club officer list on time"]
MN={7:'Jul',8:'Aug',9:'Sep',10:'Oct',11:'Nov',12:'Dec',1:'Jan',2:'Feb',3:'Mar',4:'Apr',5:'May',6:'Jun'}

rows=json.load(open(_p('data','rows.json')))
by=collections.defaultdict(dict)
meta={}
for r in rows:
    mi=int(r['Month End'][5:7])
    by[(r['Club No'],r['Program Year'])][mi]=r
    meta[r['Club No']]=(r['Club Name'],r['Division'],r['Area'])

def _i(v):
    try: return int(v)
    except Exception: return None

clubs=[]
for cid in sorted(meta,key=lambda c:meta[c][0].lower()):
    nm,dv,ar=meta[cid]
    ydat={}
    for py in PYS:
        mm=by.get((cid,py))
        if not mm: continue
        series=[(_i(mm[m]['DCP Goals Met']) if m in mm else None) for m in MORD]
        fin=mm.get(6)
        ydat[py]={"s":series,
                  "f":_i(fin['DCP Goals Met']) if fin else None,
                  "st":(fin['DCP Status'] if fin else "") or "",
                  "mb":_i(fin['Membership Base']) if fin else None,
                  "md":_i(fin['Membership To Date']) if fin else None,
                  "g":[_i(fin[g]) for g in GOALS] if fin else None}
    clubs.append({"n":cid,"m":nm,"d":dv,"a":ar,"y":ydat})

imp=[];dec=[]
for c in clubs:
    for a,b in zip(PYS,PYS[1:]):
        pa=c['y'].get(a,{}).get('f'); pb=c['y'].get(b,{}).get('f')
        if pa is None or pb is None: continue
        rec={"n":c['n'],"m":c['m'],"d":c['d'],"a":c['a'],"fy":a,"ty":b,
             "fd":pa,"td":pb,"ch":pb-pa,"st":c['y'][b]['st']}
        if pa<5 and pb>pa: imp.append(rec)
        if pa>5 and pb<pa: dec.append(rec)
imp.sort(key=lambda r:-r['ch']); dec.sort(key=lambda r:r['ch'])

out={"years":PYS,"goals":GOALS,"months":[MN[m] for m in MORD],
     "clubs":clubs,"imp":imp,"dec":dec,
     "generated":"2026-08-21","source":"dashboards.toastmasters.org — District 21"}
p=_p('docs','data.json')
json.dump(out,open(p,'w'),separators=(',',':'))
print(f"wrote {p}  {_os.path.getsize(p)/1024:.0f} KB  clubs={len(clubs)} imp={len(imp)} dec={len(dec)}")
