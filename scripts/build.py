"""Parse the cached pages into one flat row per club per month-end.

Writes data/rows.json, which every downstream script reads. Nothing here
touches the network — re-run it freely after changing parse.py.
"""
import os, sys, gzip, json, calendar

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C
import parse as P

# Column headings for the report, which follow the club report's own wording
# rather than the shorter internal names in common.ROW_NAMES.
GOAL_COLUMNS = [
    "Level 1 awards", "Level 2 awards", "More Level 2 awards", "Level 3 awards",
    "Level 4, Path Completion, or DTM award",
    "One more Level 4, Path Completion, or DTM award",
    "New members", "More new members",
    "Club officer roles trained June-August",
    "Club officer roles trained November-February",
    "Membership-renewal dues on time", "Club officer list on time",
]

MONTH = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun",
         "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def read_cached(club_id, program_year, month):
    path = os.path.join(C.CACHE, f"{club_id}_{program_year}_{month:02d}.html.gz")
    if not os.path.exists(path):
        return None
    try:
        with gzip.open(path, "rt", encoding="utf-8", errors="replace") as fh:
            return fh.read()
    except Exception:
        return None


def row_for(club_id, name, program_year, month, year, parsed):
    goals = parsed["goals"]
    todate = [(goals[i]["todate"] if i < len(goals) else "") for i in range(12)]
    return {
        "Club No": club_id,
        "Club Name": name,
        "Division": parsed.get("division", ""),
        "Area": parsed.get("area", ""),
        "Program Year": program_year,
        "Month": f"{MONTH[month]} {year}",
        "Month End": f"{year}-{month:02d}-{calendar.monthrange(year, month)[1]}",
        "Sort Key": f"{year}{month:02d}",
        "As Of": parsed.get("asof") or "",
        "DCP Status": parsed.get("status") or "",
        "Membership Base": parsed.get("mem_base"),
        "Membership To Date": parsed.get("members"),
        "Net Growth": parsed.get("net_growth"),
        "Club Success Plan": parsed.get("csp", ""),
        "DCP Goals Met": parsed.get("goals_met"),
        **{GOAL_COLUMNS[i]: todate[i] for i in range(12)},
    }


def main():
    rows, missing = [], 0
    for club_id, name in C.load_clubs():
        for program_year in C.program_years():
            for month, year in C.months_of(program_year):
                page = read_cached(club_id, program_year, month)
                if page is None:
                    missing += 1
                    continue
                parsed = P.parse(page)
                # a club that did not exist that month returns a shell page
                if parsed.get("goals_met") is None and not parsed.get("goals"):
                    continue
                rows.append(row_for(club_id, name, program_year, month, year, parsed))

    print(f"parsed rows={len(rows)} missing_files={missing}")
    with open(C.p("data", "rows.json"), "w", encoding="utf-8") as fh:
        json.dump(rows, fh)


if __name__ == "__main__":
    main()
