"""Shared ground for every script in this repo.

Anything that more than one script needs to agree on lives here: where the
repo is, which district and which years we are reporting, the shape of the
Distinguished Club Program, and how to talk to the dashboard.

Nothing here is specific to District 21 — that lives in config.json.
"""
import os, io, csv, json, time, calendar, datetime, urllib.request
try:
    from zoneinfo import ZoneInfo
except ImportError:                     # pragma: no cover - Python < 3.9
    ZoneInfo = None

# ---------------------------------------------------------------- paths ----
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def p(*parts):
    """A path relative to the repo root, so scripts run from any directory."""
    return os.path.join(ROOT, *parts)


# --------------------------------------------------------------- config ----
with open(p("config.json"), encoding="utf-8") as fh:
    CONFIG = json.load(fh)

DISTRICT = str(CONFIG["district"]).strip()
DISTRICT_NAME = CONFIG.get("district_name") or f"District {DISTRICT}"
SITE = CONFIG.get("site", {})
OUTPUT = CONFIG.get("output", {})

TIMEZONE = CONFIG.get("timezone") or "UTC"


def tz():
    """The district's own timezone, so timestamps read local to its officers."""
    if ZoneInfo is None:
        return None
    try:
        return ZoneInfo(TIMEZONE)
    except Exception:
        return None


def now_local():
    """Timezone-aware now, in the district's timezone."""
    return datetime.datetime.now(tz() or datetime.timezone.utc)


def today_local():
    return now_local().date()


def stamp(fmt="%Y-%m-%d %H:%M %Z"):
    """A build timestamp a reader in the district will recognise."""
    return now_local().strftime(fmt).strip()


CACHE = p("data", "cache")        # finished years, one page per club-month
LIVE_CACHE = p("data", "live")    # the open year


# ---------------------------------------------------------------- years ----
def program_years():
    """The finished program years this report covers, oldest first."""
    h = CONFIG["history"]
    start = int(h["start_year"])
    return [f"{y}-{y+1}" for y in range(start, start + int(h["years"]))]


def season_start(today=None):
    """The calendar year a program year begins in. July starts a new one."""
    today = today or today_local()
    return today.year if today.month >= 7 else today.year - 1


def current_program_year(today=None):
    s = season_start(today)
    return f"{s}-{s+1}"


def months_of(program_year):
    """(month, calendar_year) for a program year, July through June."""
    start = int(str(program_year)[:4])
    return [(m, start) for m in range(7, 13)] + [(m, start + 1) for m in range(1, 7)]


def last_day(month, year):
    """The dashboard wants M/D/YYYY, using the last day of the month."""
    return f"{month}/{calendar.monthrange(year, month)[1]}/{year}"


# ------------------------------------------------------------------ DCP ----
# Twelve rows on the club report earn ten goals: rows 9+10 (the two officer
# training windows) share one goal, and so do rows 11+12 (dues, officer list).
TARGETS = [4, 2, 2, 2, 1, 1, 4, 4, 4, 4, 1, 1]

ROW_NAMES = [
    "Level 1 awards", "Level 2 awards", "More Level 2 awards", "Level 3 awards",
    "Level 4, Path Completion or DTM", "A second Level 4, PC or DTM",
    "New members", "More new members",
    "Officers trained Jun-Aug", "Officers trained Nov-Feb",
    "Renewal dues on time", "Officer list on time",
]

# Which report rows feed each of the ten goals.
GOAL_ROWS = [[0], [1], [2], [3], [4], [5], [6], [7], [8, 9], [10, 11]]

GOAL_NAMES = [
    "Level 1 awards", "Level 2 awards", "More Level 2 awards", "Level 3 awards",
    "Level 4, Path Completion or DTM", "A second Level 4, PC or DTM",
    "New members", "More new members",
    "Club officers trained", "Dues & officer list on time",
]

# Goals needed for each recognition level, best first.
LEVELS = [(10, "Smedley"), (9, "President's"), (7, "Select"), (5, "Distinguished")]


# ------------------------------------------------------------- the club list ----
def load_clubs():
    """[(eight-digit club number, name)] — every club any covered year had."""
    out = []
    with open(p("scripts", "clubs.tsv"), encoding="utf-8") as fh:
        for line in fh:
            if not line.strip():
                continue
            num, _, name = line.rstrip("\n").partition("\t")
            out.append((num.strip().zfill(8), name.strip()))
    return out


# ------------------------------------------------------------- dashboard ----
BASE = "https://dashboards.toastmasters.org"
UA = {"User-Agent": f"Mozilla/5.0 (District {DISTRICT} DCP report)"}


def get(url, timeout=45, attempts=3):
    """Fetch a URL as text, retrying briefly. None if it never lands."""
    for attempt in range(attempts):
        try:
            req = urllib.request.Request(url, headers=UA)
            return urllib.request.urlopen(req, timeout=timeout).read().decode("utf-8", "replace")
        except Exception:
            if attempt == attempts - 1:
                return None
            time.sleep(1.5 * (attempt + 1))


def club_report_url(club_id, program_year, month=None, year=None, live=False):
    """A club report page.

    Closed years live under /{program-year}/; the open year is only served
    from the unprefixed path, and asking it for the current month can return
    an older snapshot than simply asking for the newest.
    """
    stem = f"{BASE}/ClubReport.aspx" if live else f"{BASE}/{program_year}/ClubReport.aspx"
    url = f"{stem}?id={club_id}"
    if month is not None and year is not None:
        url += f"&month={month}&day={last_day(month, year)}"
    return url


def roster_with_names(program_year=None):
    """{club number: club name} from the district export for a program year."""
    py = program_year or current_program_year()
    closed = py != current_program_year()
    stem = f"{BASE}/{py}/export.aspx" if closed else f"{BASE}/export.aspx"
    raw = get(f"{stem}?type=CSV&report=clubperformance~{DISTRICT}~~~{py}")
    if not raw:
        return None
    out = {}
    for row in csv.DictReader(io.StringIO(raw.lstrip("\ufeff"))):
        num = (row.get("Club Number") or "").strip()
        if num:
            out[num] = (row.get("Club Name") or "").strip() or f"Club {num}"
    return out or None


def sync_clubs_tsv(found):
    """Append clubs the district lists that clubs.tsv has never seen.

    New clubs charter mid-year. They appear in the district roster straight
    away, but the scrapers work from clubs.tsv, so without this a new club is
    invisible until someone edits the file by hand.
    """
    if not found:
        return []
    have = {cid for cid, _ in load_clubs()}
    added = [(n.zfill(8), nm) for n, nm in sorted(found.items()) if n.zfill(8) not in have]
    if added:
        with open(p("scripts", "clubs.tsv"), "a", encoding="utf-8") as fh:
            for num, name in added:
                fh.write(f"{num}\t{name}\n")
    return added


def live_club_list():
    """Clubs to pull for the open year: the district's roster, plus anything
    clubs.tsv knows that the roster call could not confirm.

    Roster first so a brand-new club is picked up the same day it charters;
    clubs.tsv as the fallback so a failed fetch does not empty the run.
    """
    found = roster_with_names()
    if not found:
        print("  roster unavailable; falling back to clubs.tsv")
        return load_clubs(), []
    added = sync_clubs_tsv(found)
    return [(n.zfill(8), nm) for n, nm in sorted(found.items(),
            key=lambda kv: kv[1].lower())], added


def roster(program_year=None):
    """Club numbers the district lists for a program year.

    Used to bootstrap clubs.tsv, and to hold the in-year view to the clubs
    that are actually in the district right now. Returns None rather than an
    empty set when the fetch fails, so callers can tell "no roster" from
    "a district with no clubs" and decline to filter on it.
    """
    py = program_year or current_program_year()
    closed = py != current_program_year()
    stem = f"{BASE}/{py}/export.aspx" if closed else f"{BASE}/export.aspx"
    raw = get(f"{stem}?type=CSV&report=clubperformance~{DISTRICT}~~~{py}")
    if not raw:
        return None
    ids = {
        (r.get("Club Number") or "").strip()
        for r in csv.DictReader(io.StringIO(raw.lstrip("﻿")))
    }
    ids.discard("")
    return ids or None


__all__ = [
    "ROOT", "p", "CONFIG", "DISTRICT", "DISTRICT_NAME", "SITE", "OUTPUT",
    "CACHE", "LIVE_CACHE", "TIMEZONE", "tz", "now_local", "today_local",
    "stamp", "program_years", "season_start",
    "current_program_year", "months_of", "last_day", "TARGETS", "ROW_NAMES",
    "GOAL_ROWS", "GOAL_NAMES", "LEVELS", "load_clubs", "BASE", "get",
    "club_report_url", "roster", "roster_with_names", "sync_clubs_tsv",
    "live_club_list",
]
