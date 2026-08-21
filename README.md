# District 21 — Club DCP Report

Month-by-month DCP data for 181 District 21 clubs, 2021-22 through 2025-26
(60 program-year month-ends, 10,170 rows).

## Layout

    scripts/   parse.py, scrape.py, build.py, analyze.py, clubs.tsv
    output/    District21_DCP_Report.xlsx + the three CSVs
    data/      cache/ (10,860 cached club-report pages, ~125 MB), rows.json, scrape.log
    probes/    exploratory fetches kept for reference

## Re-running

Scripts resolve paths relative to this folder, so they run from any working directory.

    python3 scripts/scrape.py    # skips anything already in data/cache — safe to re-run
    python3 scripts/build.py     # parses cache -> data/rows.json
    python3 scripts/analyze.py   # writes output/

To refresh, delete the months you want re-pulled from `data/cache/`
(files are named `<club>_<program-year>_<month>.html.gz`) and re-run all three.

## Notes

- Source is `dashboards.toastmasters.org/<year>/ClubReport.aspx`. The district-level
  CSV export only retains the year-end snapshot for closed years, so monthly history
  has to come from the per-club pages.
- The club report page changed layout in 2025-26; `parse.py` handles both versions.
- Goal wording shifted across years ("Level 5" -> "Path Completion"), so goals are
  aligned by DCP position 1-12, not by label.
- 18 clubs chartered mid-window and have fewer than 60 months of history.
