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

**[DESIGN.md](DESIGN.md) is the design reference** — tokens for both themes, the
type scale, metrics, every region's construction, the contrast audit, and the
short list of front-end strings that do not follow `config.json` yet. The design
is district-neutral: a new district is a config edit, not a redesign. Read it
before changing anything under `docs/`, and keep it level with the stylesheet.

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

`site.eyebrow` is the programme name alone. The year span after it is derived
from the data by `setEyebrow()` — the finished years plus the open one — so it
is right the morning after a year rolls. Do not write a span into the config.

**Three front-end strings do not follow the config yet**, and are wrong for any
district but the first: the in-year download filename and the scoped download
filename (both `District21_…` in `app.js`, which should read
`output.inyear_prefix`), and the `d21-theme` localStorage key in `app.js` and
`index.html`. The theme key matters if two districts ever share an origin —
they would share one another's light/dark choice. DESIGN.md lists them.

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

## Scale

Desktop renders a quarter larger, as `zoom` on `.mast`, `main` and `.foot`.
Zoom rather than larger font sizes because the layout is in px — it carries
type, spacing, borders and component sizes together. Below 768px there is no
zoom; a phone is already sized for the hand.

Three things to know before touching it:

- **Never zoom `:root`.** A `position: fixed` panel inside a zoomed root
  resolves its offsets in the scaled space and is then scaled again, which
  walks the club drawer off the bottom of the screen. The drawer box is left
  unzoomed and only `.detail > *` scales, at 1.4.
- **The rule must stay at the end of the stylesheet.** Media queries add no
  specificity, so while it sat at the top the base `.detail` rule 160 lines
  below silently beat its overrides.
- **`vh` inside a zoomed element is resolved before scaling**, so `82vh`
  renders at 102% of the screen. Divide by the zoom, or set the cap on an
  unzoomed ancestor.

Grid column counts inside the drawer are fixed to factors of eight rather than
`auto-fit`, which lands on seven at most desktop widths and orphans the eighth
card on a row of its own.

Section and card headings are Title Case: articles, short prepositions and
conjunctions stay lowercase unless they open the heading.

Each section header is a heading row (heading + a mono context chip), one
imperative instruction line of at most twenty words, and a `How to read this
section` disclosure holding the caveats. The instruction line is measured to
hold **one line** — the 52ch the handoff specified broke every one of them in
two. If a line still wraps, cut it rather than widening the measure. The disclosure is a native
`<details>` so it needs no JS; a `beforeprint` handler opens every one and
`afterprint` closes the ones it opened.

Area cards flow in CSS **columns**, not a grid: a fixed `repeat(3, 1fr)` with
variable-height cards breaks its row and leaves a hole two columns wide in
every division. The column count follows the number of areas (`data-n` on
`.areas`), because column balancing fills greedily — four cards across three
columns lands 2-2-0 and empties the third.

Both wide tables pin their first cell on a phone (`.stick`). Pin the cell, not
the table, give it an **opaque** background — a transparent sticky cell lets the
scrolling figures show through — and a hairline on its right edge, which is what
makes it read as a rail rather than a rendering fault.

## Brand

Type and colour follow the Toastmasters International Brand Manual.

**Typefaces.** Gotham (headings) and Myriad Pro (body) are licensed, so the
manual's own free alternates are used: **Montserrat** for headings and
**Source Sans 3** for body, with Arial and Segoe UI — the manual's tertiary
faces — behind them in the stack. IBM Plex Mono stays for tabular figures and
club numbers; the manual does not govern monospace.

**Palette** (Brand Manual p.14):

| | | |
|---|---|---|
| True Maroon | `#772432` | primary — `--maroon`, the "act here" colour |
| Loyal Blue | `#004165` | primary — `--ink`, all body text and headers |
| Cool Gray | `#A9B2B1` | primary — every neutral is a tint of it |
| Happy Yellow | `#F2DF74` | accent — `--accent`, highlights only |

Happy Yellow is never a status fill. It measures 1.35:1 against a white card,
so a yellow lamp would have no shape. Green, amber and red stay functional
colours: the manual does not legislate status, and the board's traffic-light
reading depends on the three staying distinct.

## Colour

Tokens live in `styles.css`, with a `:root[data-theme="dark"]` branch so an
explicit choice beats the system setting.

**Maroon is the interactive colour; the traffic lights are status only.**
`--maroon` is a fill and always takes white text. `--maroon-ink` is the brand
read as type — links, eyebrows, disclosure triggers, the hero italic. Never
write `--maroon` into a `color:`; three places in `app.js` did, and they
measured 2:1.

Each signal colour is a **triple**: `--green` is the fill, `--green-on` is the
text that sits on that fill, `--green-ink` is the same status set as type
against the page. Amber never takes white — that pairing measured near 2:1. The
fills are the same values in both themes: one hue per status, only lightness
moves, so the two themes do not read as different products.

`ink()` and `on()` in `app.js` map a fill to its two counterparts, so anything
written into a `color:` goes through one of them. If you add a new coloured
label, use them or an `-ink` token, then re-run the contrast audit: walk the
text elements, compare computed colour against the nearest painted background,
and require 4.5:1 (3:1 for large text). **Include the surface a row takes on
hover** — the fourth ink tier clears 4.5:1 on the page ground and fails on the
raised one, which is how `--ink4` got its value. Both themes should report zero
failures.

Two values sit a shade off the design handoff for that reason, and the hue is
unchanged in both: `--maroon-ink` (the handoff's `#C05263` measures 4.14:1 on
the ground, not the 6.1:1 it claims) and `--red` (white on `#D2564F` measures
4.08:1, and the lamps carrying it are small bold type, not large).

Colour appears only where it decides something. Numerals in tables stay
`--ink`; a figure needing a status takes an 8px dot beside it. Saturated fills
belong to score badges, bars and pips. Monospace carries numbers, dates and
IDs — words go to the sans.

There are no shadows; `--shadow` is `none` in both themes. Elevation is
`--card` against `--paper` plus a hairline.

## Contact form

The site is static, so it has no way to send mail on its own. The form's
behaviour follows `site.contact_endpoint` in config.json:

- **blank** (today) — the message is handed to the sender's own mail client
  via `mailto:`, addressed to `site.contact_email` with the subject prefixed
  by `site.contact_tag`. No account, no key, works immediately.
- **set** — the form POSTs JSON `{name,email,subject,message}` to that URL
  and the sender never leaves the page. Point it at a form service or a small
  Worker; no code changes are needed.

The spam check is arithmetic plus a hidden field no person can see. That stops
naive bots. It is **not** a verified captcha — Turnstile or reCAPTCHA need a
server to check the token, which this site does not have. Wiring an endpoint is
what makes real verification possible.

The address is never published as text. `gen_site_data.py` encodes it into
data.json and `contactCfg()` decodes it only at the moment of use, so a
harvester crawling the static files finds nothing matching an email pattern.
That is obfuscation, not secrecy — anyone reading the code can decode it. Only
an endpoint keeps the address off the client entirely.

The POST body carries no recipient. A client-supplied `to` would let anyone who
found the endpoint URL mail arbitrary addresses through it; the destination
belongs in the endpoint's own configuration.

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
