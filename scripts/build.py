import os,gzip,calendar,csv,json
import os as _os
_ROOT=_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
def _p(*a): return _os.path.join(_ROOT,*a)

import parse as P

CACHE=_p("data","cache")
GOALS=["Level 1 awards","Level 2 awards","More Level 2 awards","Level 3 awards",
"Level 4, Path Completion, or DTM award","One more Level 4, Path Completion, or DTM award",
"New members","More new members","Club officer roles trained June-August",
"Club officer roles trained November-February","Membership-renewal dues on time",
"Club officer list on time"]
PYS=["2021-2022","2022-2023","2023-2024","2024-2025","2025-2026"]
def pymonths(py):
    s=int(py[:4]); return [(m,s) for m in range(7,13)]+[(m,s+1) for m in range(1,7)]
MNAME=["","Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]

clubs=[l.rstrip('\n').split('\t') for l in open(_p('scripts','clubs.tsv')) if l.strip()]
clubs=[(n.zfill(8),nm) for n,nm in clubs]

rows=[];missing=0
for cid,nm in clubs:
    for py in PYS:
        for m,y in pymonths(py):
            f=os.path.join(CACHE,f"{cid}_{py}_{m:02d}.html.gz")
            if not os.path.exists(f): missing+=1; continue
            try: s=gzip.open(f,'rt',encoding='utf-8',errors='replace').read()
            except Exception: missing+=1; continue
            d=P.parse(s)
            if d.get('goals_met') is None and not d.get('goals'): continue
            g=d['goals']
            vals=[(g[i]['todate'] if i<len(g) else '') for i in range(12)]
            rows.append({
              'Club No':cid,'Club Name':nm,'Division':d.get('division',''),'Area':d.get('area',''),
              'Program Year':py,
              'Month':f"{MNAME[m]} {y}",'Month End':f"{y}-{m:02d}-{calendar.monthrange(y,m)[1]}",
              'Sort Key':f"{y}{m:02d}",'As Of':d.get('asof') or '',
              'DCP Status':d.get('status') or '',
              'Membership Base':d.get('mem_base'),'Membership To Date':d.get('members'),
              'Net Growth':d.get('net_growth'),'Club Success Plan':d.get('csp',''),
              'DCP Goals Met':d.get('goals_met'),
              **{GOALS[i]:vals[i] for i in range(12)}})
print(f"parsed rows={len(rows)} missing_files={missing}")
json.dump(rows,open(_p('data','rows.json'),'w'))
