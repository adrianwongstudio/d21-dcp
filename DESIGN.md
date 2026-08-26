# Design reference — the district Club Health board

What the page is built from: tokens, type, the rules that decide where colour
goes, and each region's construction. It is written **district-neutral**. The
design carries over to any district unchanged — a new district is a
`config.json` edit, not a redesign. See *Standing it up for another district*
at the end for the three strings that do not yet follow the config.

Everything here is implemented in `docs/styles.css` and `docs/app.js`. Where
this document and the stylesheet disagree, the stylesheet is what ships — fix
whichever is wrong, and keep them together.

---

## The five rules

1. **Say it once.** A section opens with one imperative line of at most twenty
   words. Caveats, definitions and provenance go behind the disclosure. Nobody
   reads a 58-word paragraph before their first control.
2. **Maroon means "you can act here."** It is the interactive colour, not
   decoration. The traffic lights carry status and nothing else.
3. **Spend colour where it decides something.** A pip, a bar, a badge, an
   urgency chip. Not on numerals, dates, arrows and icons all at once.
4. **Mono carries numbers, dates and IDs.** Words go to the sans. A
   right-aligned two-word mono label that wraps is the worst case.
5. **Every text colour clears 4.5:1** (3:1 for large text) against the surface
   it actually sits on, in both themes — including the surface a row takes on
   hover. This outranks any value in this document.

---

## Colour

Tokens live at the top of `styles.css` in three blocks: `:root` (light), a
`prefers-color-scheme: dark` branch guarded with `:root:not([data-theme="light"])`,
and `:root[data-theme="dark"]` so an explicit choice beats the system setting.
All three carry the same token names.

### Ground and ink

| Token | Light | Dark | Job |
|---|---|---|---|
| `--paper` | `#EDF1F4` | `#0A141C` | page ground; wide-table rows |
| `--sunk` | `#E3E9ED` | `#0E1A23` | inset surface; the pinned mobile rail |
| `--card` | `#FFFFFF` | `#11202B` | raised surface: panels, cards, table headers |
| `--line` | `#CBD6DE` | `rgba(255,255,255,.09)` | hairline |
| `--line-soft` | `#DCE4EA` | `rgba(255,255,255,.06)` | row separators |
| `--ink` | `#00263A` | `#EDF3F6` | headings, numerals, primary text |
| `--ink2` | `#33505F` | `#A8BAC5` | body, deck, column labels |
| `--muted` | `#596974` | `#7B8F9C` | metadata, captions |
| `--ink4` | `#55666F` | `#758997` | the quietest tier: club numbers, window names |

`--ink4` is set by the **hover** surface, not the page ground. The handoff's
`#6C808D` clears 4.5:1 on `--paper` and fails on `--card`, which is what a row
becomes under the cursor. Check the hover state when you retune it.

### Brand

| Token | Light | Dark | Job |
|---|---|---|---|
| `--maroon` | `#8E2A3A` | `#8E2A3A` | **fill only**, always with white text |
| `--maroon-ink` | `#8A2432` | `#CB6070` | the brand as type: links, eyebrow, disclosure trigger, hero italic |
| `--maroon-wash` | 10% | 14% | active nav item |
| `--maroon-rule` | 45% | 50% | disclosure underline and panel edge |

**Never write `--maroon` into a `color:`.** Three places in `app.js` did and
measured 2:1. If you need the brand as text it is `--maroon-ink`.

`--maroon-ink` on `--card` reaches only 4.3:1 in dark. Small text on a raised
surface takes `--ink` with weight instead — that is why the drawer's
"in progress" line is not maroon.

### Status — three values each, never one

| Status | fill | text **on** the fill | text on the page (light / dark) |
|---|---|---|---|
| 5–10 goals | `--green` `#46B583` | `--green-on` `#062015` | `#1F6E4C` / `#7FD3AB` |
| 3–4 goals | `--amber` `#D9A227` | `--amber-on` `#1E1403` | `#7A5405` / `#E8BF63` |
| 0–2 goals | `--red` `#CA4B44` | `--red-on` `#FFFFFF` | `#A33128` / `#EE8B84` |

The **fills are identical in both themes** — one hue per status, only lightness
moves — so the two themes read as one product. Amber never takes white: that
pairing measured near 2:1 and is the bug this table exists to prevent.

`ink()` and `on()` in `app.js` map a fill token to its two counterparts.
Anything written into a `color:` from JS goes through one of them.

Supporting: `--dead` (closed windows), `--lampoff`, `--pip-closed`,
`--pip-open`, `--red-wash` (urgency chip ground).

There are **no shadows**; `--shadow` is `none` in both themes. Elevation is
`--card` against `--paper` plus a hairline. Nothing else.

### Where colour is allowed

- Saturated fills: score badges, bars, pips, the urgency chip.
- Status ink: a division average, a membership delta, a change column.
- Everything else is `--ink` / `--ink2` / `--muted` / `--ink4`.

Numerals in tables stay `--ink`. A figure needing a status takes an **8px dot**
beside it (`.sdot[data-sig]`). A coloured numeral at 15px is the least legible
use of colour and the worst case for the red-green deficiency that affects
roughly 8% of the male membership.

---

## Type

Three faces, loaded from Google Fonts in `index.html`: **Fraunces** (display),
**Public Sans** (text), **IBM Plex Mono** (figures).

| Role | Desktop | Mobile (≤768px) |
|---|---|---|
| Hero headline | Fraunces `clamp(32px, 4.4vw, 52px)` / 1.04, 700, `-.02em` | 30px |
| Section heading | Fraunces 38px / 1.1, 700 | 30px |
| Sub-section heading | Fraunces 30px / 1.1, 700 | 25px |
| Instruction line | Public Sans 19px / 1.5, max 88ch | 18px |
| Deck | 18px / 1.6, `--ink2`, max 62ch | 17px |
| Body, table | 14–16px / 1.5 | 16px |
| Metadata | IBM Plex Mono 11–13px | — |
| Column label | IBM Plex Mono 11px, `.1em`, uppercase | — |

**The instruction line is one sentence and holds one line.** The measure is
88ch for that reason — a 52ch cap broke every one of them in two. It still
catches anything that genuinely runs long. If a line needs two, it is too long:
cut it, don't let it wrap.

Section and card headings are Title Case — articles, short prepositions and
conjunctions stay lowercase unless they open the heading.

---

## Metrics

```
spacing   4 · 8 · 10 · 12 · 14 · 18 · 22 · 24 · 28 · 32 · 44 · 52 · 64
radius    2 pip · 3 chip · 4 nav item · 5 card, control, table shell · 6 panel
rows      masthead 64 · table header 40 · table row 56 · mobile row 54 · control 38
measure   instruction 88ch · deck/prose 62ch · disclosure 60ch
```

Desktop renders a quarter larger as `zoom` on `.mast`, `main` and `.foot` —
never on `:root`, which walks the fixed drawer off the screen. The rule sits at
the **end** of the stylesheet; media queries add no specificity, so from the top
it loses to base rules below it. Every value above is pre-zoom.

---

## Regions

### Masthead

Full-bleed, 64px, `--card` ground, hairline under. Left: the mark at 26px plus a
one-line wordmark — title in Fraunces 19px/700 baseline-aligned with the
organisation at 12px/700 uppercase `.13em` in `--muted`.

Right: **three destinations, named for the task**, then a utility cluster behind
a `padding-left: 28px` rule. Nav items are 15px/600 at `7px 14px`; the active
one is 700 `--ink` on `--maroon-wash`, set by an `IntersectionObserver` that
maps every section to one of the three anchors. Utilities are 13px `--muted`.

Below 760px the right group wraps under the wordmark and the wordmark drops a
size so it holds one line at 375px.

### Hero

Two columns, `minmax(0,1fr) 400px`, gap 64px. Left: mono eyebrow in
`--maroon-ink`, headline with the second line in `<em>` (the closing period
stays outside the em in `--ink`), deck, then a legend of three dots. Right: the
router card — four rows of `64px 1fr`, a tabular figure in `--maroon-ink` at
28px over a label and sub-label, each row an anchor to the section it names.

### Section header — the pattern for all six

```html
<div class="sechead">
  <div class="secheadrow"><h2>…</h2><span class="secchip">26–27 · open</span></div>
  <p class="instruct">One imperative sentence, ≤20 words.</p>
  <details class="howto"><summary>How to read this section</summary>
    <div class="howtobody"><p>The caveats.</p></div></details>
</div>
```

The chip is mono 12px `--muted` and is filled from the data, not the markup, so
it follows the year in view. The disclosure is a native `<details>` — it works
with JS off — and a `beforeprint` handler opens every one for a print, closing
afterwards only the ones it opened.

`.sechead.withctl` is the variant that puts controls on the heading row: the
heading block left, a `flex-wrap: nowrap` toolbar right, instruction line at
16px `--ink2`.

### The current-year table

Six columns, `table-layout: fixed`, widths on the header cells rather than a
`<colgroup>` so the mobile rules can override them:

| # | Column | Width | Treatment |
|---|---|---|---|
| 1 | Club | 250px | name 15px/700 clamped to two lines; number under it in mono 11px `--ink4`, with the plan flag beside it |
| 2 | Div | 56px | mono 14px, **14px left indent** — without it a wrapped name reads as touching the letter |
| 3 | Score | 96px | right; value 19px/800 **`--ink`**, `/10` in mono `--ink4` |
| 4 | Ten goals | 210px | ten 13px pips, gap 3, `padding-left: 24px` |
| 5 | Members | 128px | right; count 15px `--ink`, delta in a fixed 22px box, status ink |
| 6 | Next deadline | 1fr | right; urgency chip **only inside 30 days**, then date in mono, then window name in a 150px box |

Rows are 56px on `--paper` with the header raised on `--card`; at the old 76px a
screen held half as many clubs. No zebra striping. The whole row opens the
drawer.

Two things deliberately absent: the **Ceiling** column and the **Success Plan**
column. The plan is a boolean that competed with the score for a whole column;
it rides on the club line as an amber `No Club Success Plan` flag, and only when
it is missing. The ceiling lives in the drawer.

Footer: pip legend left, `N of N clubs · snapshot <date>` right in mono `--ink4`.

### Area cards

`columns: 3` with `break-inside: avoid` on each card — **not** a fixed
`repeat(3, 1fr)`, which breaks its row and leaves a hole two columns wide in
every division with four or five areas.

The count follows the number of areas via `data-n` on `.areas`, because column
balancing fills greedily: four cards across three columns lands 2-2-0 and
empties the third, where two columns land 2-2 and fill both. Drops to 2 under
1024px and 1 under 640px.

Card: `--card`, hairline, radius 5, `12px 13px`, mono 10px area label. Each club
row is a 20px circular badge (status fill + status ink) beside the name in
`--ink`. **The badge carries the colour; the name carries the ink.** Ranked most
goals to fewest, so the clubs needing help sit at the bottom.

Division header: name in Fraunces 22px, and on the right `N clubs · avg X ▾ Y`
with the average in status ink, the delta arrow in status ink, and the words
between them in the sans.

### Mobile — the pinned column

Both wide tables carry `.stick`. **Pin the cell, not the table:**

- `position: sticky; left: 0` on the club `th` and `td`
- an **opaque** background — `--sunk` for rows, `--card` for the header. A
  transparent sticky cell lets the scrolling figures show through it.
- `border-right: 1px solid var(--line)` — the hairline is what makes it read as
  a fixed rail rather than a rendering fault.
- 150px wide, name wraps to two lines rather than truncating, rows 54px
- under the name, mono 11px carrying division/area
- year columns 72px (64px under 480px), values 16px tabular

The five-year table orders its **year columns newest-first** below 768px, so the
year everyone came for is on screen before any sideways scrolling, and hides its
now-redundant Div column. The latest score takes a status dot and weight 700 —
not a coloured numeral. `matchMedia` drives the order and redraws on change.

---

## The contrast audit

Required before shipping any new coloured label, in **both** themes:

1. Walk every element with a text node; skip hidden and zero-size.
2. Composite the element's colour and every translucent background down to the
   nearest fully painted ancestor. Parse `color(srgb …)` as well as `rgb()` —
   a regex that misses the modern form reports false failures on every badge.
3. Require 4.5:1, or 3:1 where the text is ≥24px, or ≥18.66px and bold.
4. Repeat with `.stick tbody tr { background: var(--card) }` forced, which is
   the hover surface, and with the drawer and contact modal open.

Both themes report **zero failures** as shipped. Two values sit a shade off the
original handoff for this reason, hue unchanged in each: `--maroon-ink` (its
`#C05263` measures 4.14:1 on the ground, not the 6.1:1 claimed) and `--red`
(white on `#D2564F` measures 4.08:1, and the lamps carrying it are small bold
type, not large).

---

## Standing it up for another district

The design is district-neutral. Everything that names a district travels in
`config.json` → `data.json` → `applySiteConfig()` in `app.js`: page title and
description, wordmark, footer source, and the spreadsheet, repo and dashboard
links. The markup carries the current district only as fallback text.

`site.eyebrow` is now the programme name alone — **"Distinguished Club
Program"**. The year span appended after it (`· 2021–22 to 2026–27`) is derived
from the data by `setEyebrow()`, the finished years plus the open one, so it is
right the morning after a year rolls. Do not write a span into the config.

**Three strings in the front end do not follow the config yet.** They are
harmless for the district they were written for and wrong for every other one,
so fix them before the second district ships:

| Where | String | Should come from |
|---|---|---|
| `app.js` — in-year download | `District21_InYear_<py>.xlsx` | `output.inyear_prefix` |
| `app.js` — scoped downloads | `District21_<kind>_<label>_DCP.xlsx` | `output.inyear_prefix` |
| `app.js` + `index.html` — theme | `localStorage` key `d21-theme` | the district, or a shared key |

The theme key matters most if two districts are ever served from the same
origin: they would share one another's light/dark choice.

Nothing else in `styles.css` or the layout needs an edit. Run
`scripts/stamp_assets.py` **last** after any change under `docs/`.
