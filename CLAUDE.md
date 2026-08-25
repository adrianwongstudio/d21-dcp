# CLAUDE.md — Toastmasters district DCP report

Guidance for Claude Code working in this repo. It is populated with
**District 21**, but nothing in the code is: the district, the years and the
site's wording all come from `config.json`. This file explains how the pieces
fit and how to stand the same report up for another district.

## What it produces

For every club a district has had, month-by-month Distinguished Club Program
data across the finished program years, plus the open year as it stands today:

- `output/` — the five-year workbook and its CSVs
- `docs/` — a static dashboard on GitHub Pages, plus `inyear.xlsx` for area directors

## Standing it up for another district

### 1. Edit `config.json`

Everything district-specific lives here. Nothing else should need touching.

```json
{
  "district": "57",
  "district_name": "District 57",
  "timezone": "America/Chicago",
  "history": { "start_year": 2021, "years": 5 },
  "site": { "title": "...", "eyebrow": "...", "spreadsheet_url": "...", "repo_url": "..." },
  "output": { "report_xlsx": "District57_DCP_Report.xlsx", "inyear_prefix": "District57" }
}
```

The `site` block travels into `data.json` and is applied to the page at load
by `applySiteConfig()` in `docs/app.js` — title, masthead, hero eyebrow,
footer, and the spreadsheet, repo and dashboard links. The markup carries
District 21 strings only as fallbacks.

### 2. Rebuild `scripts/clubs.tsv`

**Use every year's roster, not just today's.** A list of currently active
clubs leaves every past year short, because clubs close, merge and leave.

```python
import sys; sys.path.insert(0, "scripts")
import common as C
seen = {}
for py in C.program_years():
    # roster() returns club numbers; pair them with names from the same CSV
    ...
```

In practice: pull `roster(py)` for each program year, union them, and write
`clubs.tsv` as `club_number<TAB>club_name`. Numbers may lack leading zeros —
`load_clubs()` pads to eight digits. District 21 needed 227 clubs to cover
five years, against 181 active today.

### 3. Run the pipeline

```bash
# finished years — slow, cached, rarely needs re-running
python3 scripts/scrape.py && python3 scripts/build.py \
  && python3 scripts/analyze.py && python3 scripts/gen_site_data.py

# the open year — cheap, safe to repeat
python3 scripts/scrape_live.py && python3 scripts/gen_live_data.py \
  && python3 scripts/gen_inyear_xlsx.py
```

Scripts resolve paths from the repo root, so the working directory is free.

### 4. Point GitHub Pages at `/docs`

```bash
gh api -X PUT repos/<owner>/<repo>/pages -f "source[branch]=main" -f "source[path]=/docs"
```

Two workflows keep it current, both on the **1st and 15th**:

- `refresh-inyear.yml` re-runs the open-year scripts and commits `live.json`
  and `inyear.xlsx`. Refuses to commit a run returning under fifty clubs.
- `close-year.yml` runs `close_year.py` half an hour later. For eleven months
  of the year it exits immediately; once the dashboard publishes an archive
  for the year that ended on 30 June, it folds that year into `data.json`,
  widens `config.json`, and writes the final-scores workbook.

Both need `permissions: contents: write` — the repo default is read-only, and
the workflow-level grant does override it, but verify with a manual
`workflow_dispatch` run rather than waiting a month to find out.

`config.timezone` is the district's own zone; build timestamps use it, so
"built 18:43 PDT" reads correctly to an officer rather than showing the
runner's UTC.

## Layout

```
config.json          district, years, site wording — the only file a new district edits
scripts/
  common.py          paths, config, program-year maths, DCP shape, dashboard access
  parse.py           club report HTML -> dict (two page layouts)
  scrape.py          finished years  -> data/cache/
  build.py           cache           -> data/rows.json
  analyze.py         rows.json       -> output/*.xlsx, *.csv
  gen_site_data.py   rows.json       -> docs/data.json
  scrape_live.py     open year       -> data/live/
  gen_live_data.py   live cache      -> docs/live.json
  gen_inyear_xlsx.py live.json       -> docs/inyear.xlsx
  close_year.py      a closed year   -> merged into docs/data.json + output/*_final.xlsx
  stamp_assets.py    content hashes onto the URLs index.html loads (run LAST)
docs/
  index.html         markup only
  styles.css         all styling
  app.js             all behaviour
```

`data/cache/`, `data/live/` and `data/rows.json` are gitignored and regenerate.
`docs/data.json`, `docs/live.json` and `docs/inyear.xlsx` are committed,
because Pages serves them.

**Put shared facts in `common.py`.** It already holds `TARGETS`, `ROW_NAMES`,
`GOAL_ROWS`, `GOAL_NAMES` and `LEVELS`. Redefining any of them in a script is
how the twelve-row/ten-goal rule drifts out of agreement.

## The year-end rollover

`close_year.py` moves a finished year out of the open-year view and into the
published history. It scrapes **only** the closing year and merges into the
committed `data.json`, so it runs on a fresh checkout with no `data/cache`.

- `--check` reports whether an archive exists, changing nothing
- it refuses to close the year that is still open
- it re-reads that year's roster first, so clubs that existed then are covered
- it recomputes the climbed/slipped lists over the whole history
- it writes `output/<prefix>_<year>_final.xlsx` for the district spreadsheet

**Nothing writes to Google Sheets** — no connector is wired up. The workbook
is the handoff; importing it is manual.

The merge was verified by removing 2025-2026 from `data.json`, re-closing it,
and confirming the result matched club-for-club, including both transition
lists. Do that round trip again if you change the merge.

## How the dashboard actually behaves

Read before changing the scrapers.

**The district CSV export keeps only a year-end snapshot for closed years.**
`&month=` is silently ignored for an archived year — every month returns a
byte-identical file. Monthly history has to come from the per-club pages,
which is why this is ~13k requests rather than 60.

**Per-club pages do honour `month`.** `club_report_url()` builds them; closed
years live under `/{program-year}/`, the open year only on the unprefixed
path (`/{current-year}/ClubReport.aspx` returns HTTP 500). For the open year's
*current* month, omit `month` entirely — asking for it can return a snapshot
older than the newest.

**Snapshots lag.** A month-end request returns the next snapshot, usually one
to two weeks later: asking for 31 Jul 2023 yields "As of 11-Aug-2023". Recorded
as `As Of`. Expected, not a bug.

**Divisions and areas are redrawn every July.** Abbotsford Sundown moved four
times in five years. Alignment is stored **per year** in `data.json`, and the
board groups by the year in view. Storing one alignment per club files
historical years under areas the clubs were never in.

**The open year needs the live roster.** `clubs.tsv` spans every year, so it
includes clubs that have closed — whose pages still resolve with stale
alignment. `gen_live_data.py` filters to `C.roster()` so they cannot drift
into the in-year view, and new clubs appear without editing anything.

**Scale.** `clubs × 60` for the finished years — 13,620 fetches, roughly ten
minutes at eight threads, ~150 MB cached. The open year is `clubs ×
months-elapsed`, about 70 seconds in August.

## Parsing

**Two page layouts.** `parse.py` branches on `'csp-table' in html`: the
2025-26 redesign onward, and everything before. A further redesign needs a
third branch, not edits to the existing two.

**Goal wording changes between years** ("Level 5" became "Path Completion").
Align by position 1–12, never by label.

**The "to date" cell has two classes** — `clubReportGoal` when unmet and
`clubReportGoalAchieved` when met. A regex matching only the latter runs past
the row and returns garbage.

**Twelve rows, ten goals.** Rows 9+10 (officer training) earn one goal, as do
rows 11+12 (dues, officer list) — `GOAL_ROWS` encodes this. Counting achieved
rows instead of goals matched the dashboard's own figure on 1.8% of rows; the
pairing matches 99.7%. Prefer the header figure where present.

**A goal is met at its target, not above zero.** Compare against `TARGETS`.

**Status is blank until earned**, so parse the club name with and without the
trailing `<br>`.

## Analysis

Improving and declining are computed on **year-end (June) goals met**, between
consecutive years: improving is `before < 5 and after > before`; declining is
`before > 5 and after < before`. Five is the Distinguished threshold, which is
why it is the pivot. A club can appear on both lists in different years —
that volatility is a finding, not a bug.

## Gotchas

- **Verify against a known club before trusting a run.** District 21 used club
  00000396, June 2026: Smedley Distinguished, 25 members, goals
  `5,2,2,3,1,1,4,4,6,6,2,1`. Establish an equivalent for a new district.
- **Never read a gitignored file from a script the workflow runs.**
  `gen_inyear_xlsx.py` read `data/rows.json` for prior-year context; on a
  fresh runner it is absent, so the monthly build silently dropped two
  columns. It reads the committed `docs/data.json` now.
- **Quote `gh api` URLs in zsh** — `?recursive=1` is a glob.
- **GitHub Pages caches hard.** Append `?cb=1` when checking a deploy, or you
  will verify a stale build and chase phantoms.
- **Do not let a CSS animation own an element's resting state.** A staggered
  entry animation left every lamp at `scale(.4)` wherever the animation clock
  was throttled; `playState` reads `running` with `currentTime: 0`, and no
  fill-mode setting fixes it.
- **Buttons do not stretch to fill a grid track** the way divs do.
- **Wrap long club names, don't truncate.** Ellipsis hid 27 of 180 names.
- **Don't publish `ouid` in Google Sheets URLs** — it identifies an account,
  and links resolve without it.
- **Re-run `stamp_assets.py` after anything that rewrites `docs/`, and run it
  last.** Pages caches every file for ten minutes *independently*, so after a
  deploy a browser can hold new markup beside a stale `app.js` — which looks
  exactly like a feature that shipped broken. The hashes make a deploy atomic;
  they go stale the moment a stamped file changes again.
- **Preload the JSON.** The fetches live inside `app.js`, so without the
  `<link rel="preload">` tags they cannot start until the script has
  downloaded and run — measured at 135 ms of dead time. Keep the preload and
  the fetch modes matching, or the browser downloads each file twice.
- **Downloads are xlsx only.** A CSV of the same view carries less — no
  shading, no targets, no area sheet — and offering both invites the weaker file.

## Scope

The scripts read a public dashboard and write locally. Nothing authenticates,
and nothing writes to Google Sheets — the workbook is produced as `.xlsx` and
imported by hand.
