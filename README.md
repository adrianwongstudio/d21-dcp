# District 21 — Club DCP Report

Month-by-month Distinguished Club Program data for every club District 21 has
had across 2021-22 through 2025-26 — 226 clubs, 11,821 club-months — plus the
open program year as the dashboard reports it today.

Published at **https://adrianwongstudio.github.io/d21-dcp/**

## Layout

    config.json  district, years, timezone and site wording
                 — the only file another district needs to edit
    scripts/
      common.py           paths, config, program-year maths, DCP shape, dashboard access
      parse.py            club report HTML -> dict (handles both page layouts)
      scrape.py           finished years -> data/cache/
      build.py            cache -> data/rows.json
      analyze.py          rows.json -> output/
      gen_site_data.py    rows.json -> docs/data.json
      scrape_live.py      open year -> data/live/
      gen_live_data.py    live cache -> docs/live.json
      gen_inyear_xlsx.py  live.json -> docs/inyear.xlsx
      close_year.py       folds a finished year into docs/data.json
      stamp_assets.py     content hashes onto the URLs index.html loads
      clubs.tsv           every club any covered year had
    output/    District21_DCP_Report.xlsx, the CSVs, and each closed year's finals
    docs/      the published site: index.html + styles.css + app.js,
               plus data.json, live.json and inyear.xlsx
    data/      cache/ (13,620 pages, ~125 MB), live/, rows.json — all gitignored
    probes/    exploratory fetches kept for reference

## It keeps itself current

Two GitHub Actions run on the **1st and 15th** of each month:

- **Refresh in-year data** re-pulls the open year and commits `live.json` and
  `inyear.xlsx`. It refuses to commit a run returning fewer than fifty clubs.
- **Close finished year** exits immediately unless a program year has ended and
  the dashboard has published its archive. When one has, it folds that year into
  `data.json` and writes `output/District21_<year>_final.xlsx` to import into
  the district spreadsheet.

Both can be run by hand from the repo's Actions tab. Nothing writes to Google
Sheets — the workbook is the handoff, and importing it is manual.

## Running it locally

Scripts resolve paths from this folder, so the working directory is free.

    # the finished years — slow, cached, rarely needed
    python3 scripts/scrape.py      # skips anything already cached
    python3 scripts/build.py       # -> data/rows.json
    python3 scripts/analyze.py     # -> output/
    python3 scripts/gen_site_data.py

    # the open year — about 70 seconds
    python3 scripts/scrape_live.py
    python3 scripts/gen_live_data.py
    python3 scripts/gen_inyear_xlsx.py

    python3 scripts/stamp_assets.py   # always last

`stamp_assets.py` puts a content hash on each asset `index.html` loads. Pages
caches every file for ten minutes independently, so without it a browser can
hold new markup beside a stale `app.js` — which looks exactly like a feature
that shipped broken. Run it after anything that rewrites `docs/`.

To re-pull specific months, delete them from `data/cache/` (named
`<club>_<program-year>_<month>.html.gz`) and re-run build and gen.

## What the site shows

The masthead carries three destinations named for the task — **This year**,
**Past years**, **Find a club** — with the spreadsheet, Contact and the theme
toggle demoted to a utility cluster behind a rule. The active one follows the
section in view.

Every section opens with one imperative line, at most twenty words. The
caveats, definitions and provenance notes sit behind a **How to read this
section** disclosure: a native `<details>`, so it works without JS, and every
one of them opens for a print and closes again afterwards.

**The Year in Progress** — the open year: goals achieved so far, days to 30
June, and which goals are still mathematically reachable. A goal is unreachable
once its window has shut; the two officer-training windows and the two
administrative deadlines all close mid-year, so a club's ceiling can fall below
Distinguished long before June. **The Current Year** table lists every club with
its score, ten goal pips, membership and next deadline, sortable from any column
heading. Rows are 56px, which fits roughly twice as many clubs on a screen as
the 76px rows before them. The Club Success Plan rides on the club line as a
`no plan` flag rather than taking a column of its own, and the urgency chip
appears only inside thirty days — colour where it decides something.

**The Finished Years** — every club at the close of a chosen year, grouped by
the division and area that supported it *in that year*, ranked worst-last within
each area.

**Where the Goals Are Going Missing** — goal completion district-wide, the
five-year trajectory, and division standings against the prior year.

**Who Climbed, and Who Slipped** — clubs that were under five goals and
improved, and clubs that were above five and fell back.

**Every Club, Year by Year** — searchable, with five-year sparklines.

Both wide tables pin their club column on a phone: `position: sticky` on the
first `th` and `td` with an **opaque** background and a hairline on its right
edge — a transparent sticky cell lets the scrolling figures show through it, and
the hairline is what makes it read as a rail rather than a rendering fault. The
five-year table also orders its year columns newest-first below 768px, so the
year everyone came for is on screen before any sideways scrolling.

Selecting a club anywhere opens a panel with a year picker: every year it has,
plus the open year while it is still in the district. Switching years reprints
the division and area, because those belong to the year in view.

## Downloads

Every download is a real workbook — there is no CSV, because it carried less.
`docs/inyear.xlsx` is one row per club with the twelve goal counts, membership,
next deadline and Club Success Plan, for an area director to open alongside a
club officer. Each division header and area card carries its own scoped
download, and a club's panel exports just that club.

## Contact

A **Contact** button in the masthead opens a form — name, email, subject,
message and a spam check. The subject is sent prefixed with `site.contact_tag`
("DCP-Dashboard") to `site.contact_email`.

The site is static and cannot send mail itself, so delivery follows
`site.contact_endpoint`:

- **blank** (as now) — the message is handed to the sender's own mail client,
  pre-addressed with the tagged subject. No account or key needed.
- **set** — the form POSTs `{name, email, subject, message}` to that URL and
  the sender never leaves the page. Point it at a form service or a small
  Worker; no code changes required.

The address is never published as text: `gen_site_data.py` encodes it into
data.json and the form decodes it only when a message is sent, so nothing in
`docs/` matches an email pattern. That is obfuscation, not secrecy — only an
endpoint keeps the address off the client altogether.

The POST body carries **no recipient**. A client-supplied `to` would let anyone
who found the endpoint URL relay mail through it; the destination belongs in
the endpoint's own configuration.

The spam check is an arithmetic question plus a hidden field no person can see.
That stops naive bots. It is **not** a verified captcha — Turnstile and
reCAPTCHA check their token server-side, which needs the endpoint above.

## Colour

Light and dark palettes are defined as tokens in `styles.css`, with an explicit
`[data-theme]` branch so the toggle wins over the system setting.

**Maroon is the interactive colour and the traffic lights are status only.**
`--maroon` is a fill and always takes white text; `--maroon-ink` is the same
brand read as type — links, eyebrows, disclosure triggers, the hero italic.
Nothing writes `--maroon` into a `color:`.

Each signal colour is a triple, not a value:

| | fill | text on the fill | text on the page |
|---|---|---|---|
| 5–10 goals | `--green` | `--green-on` | `--green-ink` |
| 3–4 goals | `--amber` | `--amber-on` | `--amber-ink` |
| 0–2 goals | `--red` | `--red-on` | `--red-ink` |

The fills are the same values in both themes — one hue per status, only
lightness moves — so a lamp is the same green on paper and on ink. `ink()` and
`on()` in `app.js` map a fill to its two counterparts. Amber never takes white:
it measured near 2:1 that way.

Colour appears only where it decides something. Numerals in tables stay
`--ink`; a figure that needs a status gets an 8px dot beside it, because a
coloured numeral at 15px is the least legible use of colour and the worst case
for the red-green deficiency that affects roughly 8% of the male membership.
Monospace carries numbers, dates and IDs; words go to the sans.

Every text colour clears WCAG AA (4.5:1, 3:1 for large text) against the
background it sits on — including the surface a row takes on hover — in both
themes. Re-run the audit after adding a coloured label: walk the text elements,
compare computed colour against the nearest painted background, and require
zero failures in each theme.

There are no shadows. Elevation is `--card` against `--paper` plus a hairline.

## Scale and headings

Desktop renders a quarter larger. It is applied as `zoom` on `.mast`, `main`
and `.foot` rather than by raising font sizes, because the layout is built in
px — zoom carries type, spacing, borders and component sizes together. Phones
are excluded below 768px, where 375px is already sized for the hand.

The club drawer is deliberately not zoomed as a box: it is `position: fixed`,
and zooming it resolves its offsets in the scaled space and lands it below the
screen. Its children scale instead, at 1.4, so the panel reads a step larger
than the page it covers while staying anchored.

Section and card headings are Title Case — articles, short prepositions and
conjunctions stay lowercase unless they open the heading.

## Notes

- Source is `dashboards.toastmasters.org`. The district CSV export keeps only a
  year-end snapshot for closed years, so monthly history comes from the
  per-club pages.
- The open year is **not** on the year-prefixed URL — that returns HTTP 500. It
  comes from the unprefixed `ClubReport.aspx`.
- The club report changed layout in 2025-26; `parse.py` handles both.
- Goal wording shifts between years ("Level 5" became "Path Completion"), so
  goals are aligned by DCP position 1-12, never by label.
- The report prints 12 goal rows but the DCP awards 10: the two officer-training
  rows earn one goal between them, as do the two administrative rows.
- Divisions and areas are redrawn every July. Alignment is stored per year;
  Abbotsford Sundown has sat in four different areas across five years.
- `clubs.tsv` spans every year, so it includes clubs that have closed. The open
  year takes its club list from the live district roster instead, and writes any
  newly chartered club back to the file.
- 55 of 226 clubs have fewer than 60 months of history — chartered, closed or
  suspended part-way through the window.

See `CLAUDE.md` for how to stand this up for another district.
