"""Build docs/live.json - the in-year operational view.

Three things the analysis pages cannot answer:
  1. what each club has achieved RIGHT NOW,
  2. how many days are left to act,
  3. which goals are still mathematically reachable.

The third is the whole point. Most DCP goals stay open until 30 June, but the
two officer-training windows and the two admin deadlines shut mid-year. Once
they shut, a goal is gone and no amount of effort recovers it - so a club's
ceiling can drop below Distinguished long before the year ends.
"""
import os,sys,gzip,json,calendar,datetime,collections
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import parse as P

DISTRICT="21"

def _current_roster(S):
    """Club numbers the district dashboard lists for the open program year."""
    import csv,io,urllib.request
    url=(f"https://dashboards.toastmasters.org/export.aspx?type=CSV"
         f"&report=clubperformance~{DISTRICT}~~~{S}-{S+1}")
    try:
        raw=urllib.request.urlopen(urllib.request.Request(url,
            headers={'User-Agent':'Mozilla/5.0 (D21 DCP report)'}),timeout=45).read().decode('utf-8-sig','replace')
        ids={(r.get('Club Number') or '').strip() for r in csv.DictReader(io.StringIO(raw))}
        ids={i for i in ids if i}
        return ids if len(ids)>20 else None      # too few to be a real roster; don't filter on it
    except Exception as e:
        print(f"  roster unavailable ({e}); keeping every club in clubs.tsv")
        return None


_ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def _p(*a): return os.path.join(_ROOT,*a)
LIVE=_p("data","live")

# The club report prints 12 rows, but the DCP awards only 10 goals: the two
# officer-training rows together earn one goal, and so do the two admin rows.
# Counting achieved rows instead of goals overstates almost every club.
TARGETS=[4,2,2,2,1,1,4,4,4,4,1,1]
ROWNAMES=["Level 1 awards","Level 2 awards","More Level 2 awards","Level 3 awards",
 "Level 4, Path Completion or DTM","A second Level 4, PC or DTM","New members",
 "More new members","Officers trained Jun-Aug","Officers trained Nov-Feb",
 "Renewal dues on time","Officer list on time"]
GOALS=[{"n":"Level 1 awards","r":[0]},{"n":"Level 2 awards","r":[1]},
 {"n":"More Level 2 awards","r":[2]},{"n":"Level 3 awards","r":[3]},
 {"n":"Level 4, Path Completion or DTM","r":[4]},{"n":"A second Level 4, PC or DTM","r":[5]},
 {"n":"New members","r":[6]},{"n":"More new members","r":[7]},
 {"n":"Club officers trained","r":[8,9]},{"n":"Dues & officer list on time","r":[10,11]}]
MORD=[7,8,9,10,11,12,1,2,3,4,5,6]
MN={7:'Jul',8:'Aug',9:'Sep',10:'Oct',11:'Nov',12:'Dec',1:'Jan',2:'Feb',3:'Mar',4:'Apr',5:'May',6:'Jun'}
LEVELS=[(10,"Smedley"),(9,"President's"),(7,"Select"),(5,"Distinguished")]

def eom(y,m): return datetime.date(y,m,calendar.monthrange(y,m)[1])

def windows(S):
    """Per row: (act-by date, date from which the row is provably unreachable).

    Act-by is the real Toastmasters deadline. The dead-from date is later
    because the dashboard keeps accepting late entries for a while - derived
    from when each row was last observed to increase across 10,170 historical
    rows, so we never call a goal dead while the source still moves it.
    """
    E=datetime.date(S+1,6,30); J=datetime.date(S,7,1)
    w=[(E,None,J)]*8                                 # awards + members: open all year
    return w+[
      (eom(S,8),   datetime.date(S,11,1),   datetime.date(S,6,1)),   # Jun-Aug training (tail to Oct)
      (eom(S+1,2), datetime.date(S+1,6,1),  datetime.date(S,11,1)),  # Nov-Feb training (tail to May)
      (eom(S+1,3), datetime.date(S+1,5,1),  J),                      # dues: Sep + Mar rounds
      (eom(S,12),  datetime.date(S+1,2,1),  J)]                      # officer list

def _i(v):
    try: return int(str(v).strip())
    except Exception: return None

def goal_states(vals,WIN,today,END):
    """Per DCP goal: 'm' met, 'o' still reachable, 'd' window shut.

    Split out so it can be exercised at dates other than today - nothing is
    unreachable in August, so this would otherwise ship untested.
    """
    rowmet=[(vals[i] is not None and vals[i]>=TARGETS[i]) for i in range(12)]
    st=[];why=[]
    for g in GOALS:
        if all(rowmet[i] for i in g['r']): st.append('m'); why.append('')
        else:
            blocked=[i for i in g['r'] if not rowmet[i] and WIN[i][1] and today>=WIN[i][1]]
            if blocked: st.append('d'); why.append(ROWNAMES[blocked[0]]+" window closed")
            else:
                nxt=min((WIN[i][0] for i in g['r'] if not rowmet[i]),default=END)
                st.append('o'); why.append(nxt.isoformat())
    return st,why

def main():
    today=datetime.date.today()
    S=today.year if today.month>=7 else today.year-1
    PY=f"{S}-{S+1}"; END=datetime.date(S+1,6,30)
    days_left=(END-today).days
    WIN=windows(S)
    elapsed=[(m,S if m>=7 else S+1) for m in MORD
             if (S if m>=7 else S+1,m)<=(today.year,today.month)]

    clubs=[l.rstrip('\n').split('\t') for l in open(_p('scripts','clubs.tsv')) if l.strip()]
    # clubs.tsv spans every year we hold history for, so it includes clubs that have
    # since closed or left. Their pages still resolve with stale alignment, which would
    # put them in the in-year view. The district's own roster is what counts today.
    roster=_current_roster(S)
    if roster:
        before=len(clubs)
        clubs=[c for c in clubs if c[0].zfill(8) in roster]
        print(f"  roster: {len(clubs)} clubs currently in the district ({before-len(clubs)} no longer listed)")
    clubs=[(n.zfill(8),nm) for n,nm in clubs]

    out=[];asofs=[];recon=0;nodata=[]
    for cid,nm in clubs:
        snaps={}
        for m,y in elapsed:
            f=os.path.join(LIVE,f"{cid}_{m:02d}.html.gz")
            if not os.path.exists(f): continue
            try: snaps[m]=P.parse(gzip.open(f,'rt',encoding='utf-8',errors='replace').read())
            except Exception: pass
        cur=snaps.get(elapsed[-1][0])
        if not cur or cur.get('goals_met') is None:
            nodata.append(nm); continue
        vals=[_i(cur['goals'][i]['todate']) if i<len(cur['goals']) else None for i in range(12)]
        st,why=goal_states(vals,WIN,today,END)
        hdr=_i(cur['goals_met'])
        # Newly chartered clubs get the training window they missed waived, so
        # the dashboard can credit a goal our row data says is unmet. Trust it.
        if hdr is not None and sum(x=='m' for x in st)<hdr and st[8]!='m':
            st[8]='m'; why[8]='credited (club chartered mid-window)'; recon+=1
        met=sum(x=='m' for x in st)
        ceil=met+sum(x=='o' for x in st)
        if hdr is not None and met!=hdr: met=hdr; ceil=max(ceil,met)

        mb,md=_i(cur.get('mem_base')),_i(cur.get('members'))
        ng=(md-mb) if (mb is not None and md is not None) else None
        memok=bool(md is not None and (md>=20 or (ng is not None and ng>=5)))
        best=next((n for t,n in LEVELS if ceil>=t),None)
        now =next((n for t,n in LEVELS if met>=t),None)
        series=[(_i(snaps[m]['goals_met']) if m in snaps and snaps[m].get('goals_met') is not None else None)
                for m,_ in elapsed]
        if cur.get('asof'): asofs.append(cur['asof'])
        out.append({"n":cid,"m":nm,"d":cur.get('division',''),"a":cur.get('area',''),
          "met":met,"ceil":ceil,"st":st,"why":why,"v":vals,
          "mb":mb,"md":md,"ng":ng,"memok":memok,
          "best":best,"now":now,"s":series,"asof":cur.get('asof') or "",
          "csp":cur.get('csp') or ""})

    out.sort(key=lambda c:(c['ceil'],c['met'],-len(c['m'])))
    def asof_key(a):
        try: return datetime.datetime.strptime(a,"%d-%b-%Y").date()
        except Exception: return datetime.date(1970,1,1)
    asof=max(asofs,key=asof_key) if asofs else ""

    # Reachability alone is uninformative early in the year - nothing has died
    # yet. What bites is the NEXT window to shut, and who loses a goal when it
    # does. That is the number an operations page exists to surface.
    close=[]
    for i in (8,9,10,11):
        act=WIN[i][0]
        if act<today: continue
        opens=WIN[i][2]
        n=sum(1 for c in out if c['v'][i] is not None and c['v'][i]<TARGETS[i])
        if n: close.append({"lbl":ROWNAMES[i],"date":act.isoformat(),
                            "days":(act-today).days,"clubs":n,
                            "open":today>=opens,"opens":opens.isoformat()})
    close.sort(key=lambda x:x['days'])
    for c in out:
        nd=[(WIN[i][0],ROWNAMES[i]) for g in GOALS for i in g['r']
            if not (c['v'][i] is not None and c['v'][i]>=TARGETS[i]) and WIN[i][0]>=today]
        c['nd'],c['ndl']=(min(nd)[0].isoformat(),min(nd)[1]) if nd else ("","")

    agg={"clubs":len(out),
      "dist_now":sum(1 for c in out if c['met']>=5),
      "dist_live":sum(1 for c in out if c['met']<5 and c['ceil']>=5),
      "dist_out":sum(1 for c in out if c['ceil']<5),
      "at_risk":sum(1 for c in out if c['ceil']<5),
      "train_dead":sum(1 for c in out if c['st'][8]=='d'),
      "train_open":sum(1 for c in out if c['st'][8]=='o'),
      "memok":sum(1 for c in out if c['memok']),
      "avg_met":round(sum(c['met'] for c in out)/max(len(out),1),2),
      "close":close}

    doc={"py":PY,"asof":asof,"today":today.isoformat(),"end":END.isoformat(),
      "days":days_left,"months":[MN[m] for m,_ in elapsed],
      "acts":[WIN[i][0].isoformat() for i in range(12)],
      "targets":TARGETS,"rows":ROWNAMES,
      "goals":[g['n'] for g in GOALS],"clubs":out,"agg":agg,
      "generated":datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
      "source":"dashboards.toastmasters.org - District 21"}
    p=_p('docs','live.json')
    json.dump(doc,open(p,'w'),separators=(',',':'))
    print(f"wrote {p}  {os.path.getsize(p)/1024:.0f} KB")
    print(f"  {PY}  as of {asof}  {days_left} days to {END}")
    print(f"  clubs={agg['clubs']}  waiver-reconciled={recon}  no-data={len(nodata)} {nodata}")
    print(f"  distinguished now={agg['dist_now']}  still reachable={agg['dist_live']}  out={agg['dist_out']}")
    print(f"  training goal: open={agg['train_open']} dead={agg['train_dead']}")
    for c in close:
        tail=f"{c['clubs']} clubs short" if c['open'] else f"window opens {c['opens']}"
        print(f"  closing in {c['days']:>4}d  {c['date']}  {c['lbl']:<26} {tail}")

if __name__=='__main__': main()
