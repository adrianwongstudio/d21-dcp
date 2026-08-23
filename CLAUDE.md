# CLAUDE.md — Toastmasters district DCP report

Guidance for Claude Code working in this repo. It is currently populated with
**District 21**, but nothing here is specific to that district except
`scripts/clubs.tsv` and a handful of labels. This file explains how to
reproduce the whole thing for any district.

## What this produces

For every club in a district, month-by-month Distinguished Club Program data
across five program years (60 month-ends), and from that:

- `output/District21_DCP_Report.xlsx` — README, Monthly Data, Year-End Summary,
  Improving Clubs, Declining Clubs, Action List
- `output/*.csv` — the same content as flat files
- `docs/` — a static dashboard published via GitHub Pages

## Reproducing for another district

The scraper never sends a district id. It works purely from a list of club
numbers, so **swapping districts means swapping `scripts/clubs.tsv`.**

### 1. Build the club list

Pull the district's club roster from the year-prefixed export. Use a **closed**
program year — the unprefixed `export.aspx` is context-dependent and can return
a header with no rows.

```bash
curl -s "https://dashboards.toastmasters.org/2025-2026/export.aspx?type=CSV&report=clubperformance~04~~~2025-2026" -o roster.csv
```

Replace `04` with the zero-padded district number. Verified working for
districts 04 (81 clubs), 21 (194) and 57 (107).

Then write `scripts/clubs.tsv` as `club_number<TAB>club_name`, one per line.
Club numbers may be given without leading zeros; the scraper pads them to eight
digits itself (`n.zfill(8)`).

### 2. Set the program years

Five constants must agree, or rows will silently go missing:

| File | Constant |
|---|---|
| `scripts/scrape.py` | `for start in [2021,2022,2023,2024,2025]` |
| `scripts/build.py` | `PYS=[...]` |
| `scripts/analyze.py` | `PYS=[...]` |
| `scripts/gen_site_data.py` | `PYS=[...]` |

A program year runs **July → June** and is written `2025-2026`. Only closed
years are reliable; see "Current year" below.

### 3. Run the pipeline

```bash
python3 scripts/scrape.py && python3 scripts/build.py && python3 scripts/analyze.py && python3 scripts/gen_site_data.py
```

Scripts resolve paths from their own location, so the working directory does
not matter.

### 4. Update the labels

Cosmetic, but they are hardcoded:

- `scripts/analyze.py` — sheet title, README rows, output filename, and the
  `Action List <year>` tab name
- `scripts/gen_site_data.py` — the `source` string and `generated` date
- `docs/index.html` — masthead, hero copy, footer links, spreadsheet URL, and
  the GitHub repo URL

## The pipeline

```
scrape.py         → data/cache/<club>_<program-year>_<month>.html.gz   (one page per club-month)
build.py          → data/rows.json      (parses the cache; uses parse.py)
analyze.py        → output/*.xlsx, *.csv
gen_site_data.py  → docs/data.json      (compact extract for the dashboard)
parse.py          → shared HTML parser, imported by build.py
```

`data/cache/` and `data/rows.json` are gitignored. Both regenerate.

## How the data source actually behaves

These cost real time to discover. Read before changing the scraper.

**The district CSV export only keeps a year-end snapshot for closed years.**
Passing `&month=` to `export.aspx` for an archived year is silently ignored —
every month returns a byte-identical file. The archived district page's date
picker confirms it: for 2023-24 it offers only 12 Jun – 19 Jul 2024. Monthly
history therefore has to come from the per-club pages, which is why this is
~11k requests rather than 60.

**Per-club pages do honour `month`.** The working URL shape:

```
https://dashboards.toastmasters.org/{program-year}/ClubReport.aspx?id={8-digit}&month={M}&day={M}/{last-day}/{YYYY}
```

`month` is the calendar month (7–12 then 1–6), and `day` is the last day of that
calendar month.

**Snapshots lag.** A month-end request returns the dashboard's next snapshot,
typically 1–2 weeks later — asking for 31 Jul 2023 yields "As of 11-Aug-2023".
The parser records this as the `As Of` column. It is expected, not a bug.

**Current year.** `/{current-program-year}/ClubReport.aspx` returns HTTP 500 —
the archive path only exists once a year closes. Scope to closed years, or
handle the unprefixed path separately.

**Scale.** `clubs × 60` requests. District 21 was 10,860 fetches ≈ 8 minutes at
8 threads, producing a 125 MB cache. `scrape.py` skips anything already cached,
so it is safe to re-run and cheap to resume. To refresh specific months, delete
those files from `data/cache/` and re-run all four scripts.

## Parsing

**Two page layouts.** The club report was redesigned for 2025-26. `parse.py`
branches on `'csp-table' in html`:

- 2025-26 onward — membership in `sub-table-header-item`, goals met in a
  `<th>` under `<span>Goals</span>`, division/area in a flex row
- through 2024-25 — `chart_table_big_numbers` spans

Any new redesign needs a third branch, not edits to the existing ones.

**Goal labels change between years.** "Level 5" became "Path Completion";
"Club officers trained" became "Club officer roles trained". **Align goals by
position 1–12, never by label.** The order is stable:

```
1 Level 1 awards                    7  New members
2 Level 2 awards                    8  More new members
3 More Level 2 awards               9  Officers trained Jun–Aug
4 Level 3 awards                    10 Officers trained Nov–Feb
5 Level 4 / Path Completion / DTM   11 Membership-renewal dues on time
6 A second Level 4 / PC / DTM       12 Club officer list on time
```

Targets, used to decide whether a goal was met: `[4,2,2,2,1,1,4,4,4,4,1,1]`.

**The "to date" cell has two classes** — `clubReportGoal` when unmet and
`clubReportGoalAchieved` when met. A regex matching only the latter will
greedily span rows and return garbage.

**Status is blank until earned.** The `<h2>` carries a `<br>` and the
distinguished status only once the club qualifies, so parse the club name with
and without it.

**Clubs chartered mid-window have fewer than 60 months.** In District 21, 18
clubs, and one (IA Vancouver) had no month-end in the window at all — 181 clubs
listed, 180 with data. Absent months are legitimately absent; do not backfill.

## Analysis definitions

Both are computed on **year-end (June) `DCP Goals Met`**, comparing consecutive
program years:

- **Improving** — prior year `< 5` and current year higher than prior
- **Declining** — prior year `> 5` and current year lower than prior

Five is the Distinguished threshold, which is why it is the pivot. Note a club
can appear on both lists in different years; that volatility is a real finding
worth surfacing, not a bug.

## The dashboard

`docs/index.html` is a single self-contained file that fetches `docs/data.json`
(~150 KB). No build step and no external JS.

- **Board** — clubs grouped Division → Area, each area ranked by score
  descending so struggling clubs fall to the bottom. Each row is a lamp
  (goals met) plus the club name.
- **Charts** — goal completion worst-first, five-year trajectory by band,
  division standings against the prior year.
- **Movement** — climbed/slipped tables per year transition.
- **Clubs** — searchable table with five-year sparklines.

Signal thresholds: green `≥5`, amber `3–4`, red `0–2`.

### Deploying

Pages serves from `main` branch `/docs`:

```bash
gh api -X PUT repos/<owner>/<repo>/pages -f "source[branch]=main" -f "source[path]=/docs"
```

If Pages renders the README instead of the dashboard, the source path is still
`/` — that PUT fixes it. Builds take 45–90 s after a push.

## Gotchas

- **Verify against a known club before trusting a run.** District 21 used club
  00000396, June 2026: Smedley Distinguished, 25 members, goals
  `5,2,2,3,1,1,4,4,6,6,2,1`. Establish an equivalent for a new district.
- **Quote `gh api` URLs in zsh.** `?recursive=1` is a glob and will fail
  unquoted.
- **GitHub Pages caches hard.** After deploying, append a cache-busting query
  (`?cb=1`) before checking, or you will verify a stale build and chase
  phantoms.
- **Do not let a CSS animation own an element's resting state.** A staggered
  entry animation on the board left every lamp at `scale(.4)` wherever the
  animation clock was throttled. `playState` reads `running` with
  `currentTime: 0`, and no `fill-mode` value fixes it.
- **Buttons do not stretch to fill a grid track** the way divs do.
- **Wrap long club names, don't truncate them.** Ellipsis hid 27 of 180 names.
- **Don't publish `ouid` in Google Sheets URLs** — it identifies a specific
  account and links resolve without it.

## Scope

The scripts read from a public dashboard and write locally. Nothing here
authenticates, and nothing writes to Google Sheets — the workbook is produced
as `.xlsx` and imported by hand. If a Google Sheets connector is available,
that import could be automated from `data/rows.json`.
