"""Compact the finished years into docs/data.json for the dashboard.

Keys are short because the browser downloads this file: n=number, m=name,
d/a=division/area, y=per-year, f=final goals, s=monthly series.
"""
import os, sys, json, datetime, collections

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C
from build import GOAL_COLUMNS

MONTH_ORDER = [7, 8, 9, 10, 11, 12, 1, 2, 3, 4, 5, 6]
MONTH_NAME = {7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec",
              1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun"}

DISTINGUISHED = 5   # goals that earn Distinguished, and the pivot both lists turn on



def _site_for_publishing(site):
    """Copy of the site config with the contact address encoded, not plain."""
    import base64
    out = dict(site)
    addr = out.pop("contact_email", "")
    if addr:
        out["contact_email_enc"] = base64.b64encode(addr[::-1].encode()).decode()
    return out


def as_int(v):
    try:
        return int(v)
    except Exception:
        return None


def load_rows():
    """rows.json indexed as [club][program year][month] -> row."""
    with open(C.p("data", "rows.json"), encoding="utf-8") as fh:
        rows = json.load(fh)
    by = collections.defaultdict(dict)
    meta = {}
    for r in rows:
        month = int(r["Month End"][5:7])
        by[(r["Club No"], r["Program Year"])][month] = r
        meta[r["Club No"]] = (r["Club Name"], r["Division"], r["Area"])
    return by, meta


def year_record(months):
    """One club's year: the monthly trace plus its June year-end state."""
    final = months.get(6)
    series = [(as_int(months[m]["DCP Goals Met"]) if m in months else None)
              for m in MONTH_ORDER]
    if not final:
        return {"s": series, "f": None, "st": "", "mb": None, "md": None,
                "g": None, "csp": "", "d": "", "a": ""}
    return {
        "s": series,
        "f": as_int(final["DCP Goals Met"]),
        "st": final["DCP Status"] or "",
        "mb": as_int(final["Membership Base"]),
        "md": as_int(final["Membership To Date"]),
        "g": [as_int(final[g]) for g in GOAL_COLUMNS],
        "csp": final.get("Club Success Plan") or "",
        # divisions are redrawn every July, so alignment belongs to the year
        "d": final["Division"] or "",
        "a": final["Area"] or "",
    }


def transitions(clubs, years):
    """Clubs that climbed from under the threshold, and that slipped from above it."""
    climbed, slipped = [], []
    for c in clubs:
        for before, after in zip(years, years[1:]):
            was = c["y"].get(before, {}).get("f")
            now = c["y"].get(after, {}).get("f")
            if was is None or now is None:
                continue
            # the alignment that applied in the year being reported, not the
            # club's current one — most clubs have moved at least once
            end = c["y"][after]
            rec = {"n": c["n"], "m": c["m"],
                   "d": end.get("d") or c["d"], "a": end.get("a") or c["a"],
                   "fy": before, "ty": after, "fd": was, "td": now,
                   "ch": now - was, "st": end["st"]}
            if was < DISTINGUISHED and now > was:
                climbed.append(rec)
            if was > DISTINGUISHED and now < was:
                slipped.append(rec)
    climbed.sort(key=lambda r: -r["ch"])
    slipped.sort(key=lambda r: r["ch"])
    return climbed, slipped


def main():
    years = C.program_years()
    by, meta = load_rows()

    clubs = []
    for club_id in sorted(meta, key=lambda c: meta[c][0].lower()):
        name, division, area = meta[club_id]
        per_year = {py: year_record(by[(club_id, py)])
                    for py in years if by.get((club_id, py))}
        clubs.append({"n": club_id, "m": name, "d": division, "a": area, "y": per_year})

    climbed, slipped = transitions(clubs, years)

    out = {
        "years": years,
        "goals": GOAL_COLUMNS,
        "months": [MONTH_NAME[m] for m in MONTH_ORDER],
        "clubs": clubs,
        "imp": climbed,
        "dec": slipped,
        "district": C.DISTRICT_NAME,
        "district_id": C.DISTRICT,
        # The address is obfuscated on its way into the published JSON. Address
        # harvesters crawl static files for anything matching an email pattern;
        # this defeats that. It is not secrecy — anyone reading the code can
        # decode it — but it keeps the address out of a scraper's regex.
        "site": _site_for_publishing(C.SITE),
        "generated": C.today_local().isoformat(),
        "source": f"dashboards.toastmasters.org — {C.DISTRICT_NAME}",
    }
    dest = C.p("docs", "data.json")
    with open(dest, "w", encoding="utf-8") as fh:
        json.dump(out, fh, separators=(",", ":"))
    print(f"wrote {dest}  {os.path.getsize(dest)/1024:.0f} KB  "
          f"clubs={len(clubs)} imp={len(climbed)} dec={len(slipped)}")


if __name__ == "__main__":
    main()
