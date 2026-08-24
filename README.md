# District 21 — Club DCP Report

Month-by-month DCP data for 181 District 21 clubs, 2021-22 through 2025-26
(60 program-year month-ends, 10,170 rows).

## Layout

    scripts/   parse.py, scrape.py, build.py, analyze.py, clubs.tsv
               scrape_live.py, gen_live_data.py, gen_inyear_xlsx.py  (open year)
    output/    District21_DCP_Report.xlsx + the three CSVs
    docs/      the published dashboard: index.html, data.json, live.json, inyear.xlsx
    data/      cache/ (10,860 cached club-report pages, ~125 MB), live/, rows.json, scrape.log
    probes/    exploratory fetches kept for reference

## Re-running

Scripts resolve paths relative to this folder, so they run from any working directory.

    python3 scripts/scrape.py    # skips anything already in data/cache — safe to re-run
    python3 scripts/build.py     # parses cache -> data/rows.json
    python3 scripts/analyze.py   # writes output/

The five closed years above change only when a year ends. The open year is separate
and cheap — roughly 25 seconds in August, growing to about three minutes by June:

    python3 scripts/scrape_live.py     # the current program year only
    python3 scripts/gen_live_data.py   # -> docs/live.json
    python3 scripts/gen_inyear_xlsx.py # -> docs/inyear.xlsx

Run those three, then commit `docs/live.json` and `docs/inyear.xlsx` to refresh the
site. The page shows the dashboard's snapshot date, so a stale build is visible
rather than silent.

To refresh, delete the months you want re-pulled from `data/cache/`
(files are named `<club>_<program-year>_<month>.html.gz`) and re-run all three.

## The in-year view

The dashboard's first section covers the **open** program year: goals achieved so
far, days remaining until 30 June, and which goals are still mathematically
reachable. A goal is unreachable once the window it lived in has shut — the two
officer-training windows and the two administrative deadlines all close mid-year,
so a club's ceiling can drop below Distinguished long before June.

`docs/inyear.xlsx` is the same data as a workbook — one row per club with the
twelve goal counts, membership, ceiling and next deadline, filterable by division
and area, for an area director to open alongside a club officer. Each division
header and area card on the board carries its own download for the clubs in that
patch — scoped to the *current* roster, since clubs realign between program years,
with any club that moved named in the file. The club table
also exports the current filtered view as CSV, and each club's detail panel has
an **Excel** button that downloads just that club: the open year, every goal with
its target and act-by date, and the five closed years behind it.

## Notes

- Source is `dashboards.toastmasters.org/<year>/ClubReport.aspx`. The district-level
  CSV export only retains the year-end snapshot for closed years, so monthly history
  has to come from the per-club pages.
- The club report page changed layout in 2025-26; `parse.py` handles both versions.
- Goal wording shifted across years ("Level 5" -> "Path Completion"), so goals are
  aligned by DCP position 1-12, not by label.
- 18 clubs chartered mid-window and have fewer than 60 months of history.
- The club report prints 12 goal rows but the DCP awards 10 goals: the two officer-training
  rows earn one goal between them, as do the two administrative rows. Counting rows instead
  of goals matches the dashboard on under 2% of rows; the pairing matches 99.7%.
- The open year is not on the year-prefixed URL (it returns HTTP 500). It comes from the
  unprefixed `ClubReport.aspx`, which still honours `month`.
