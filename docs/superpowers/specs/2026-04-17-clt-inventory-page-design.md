# CLT Inventory Page — Design

**Date:** 2026-04-17
**Status:** Approved (design)
**Owner:** tfalcon

## Goal

Publish a new page at `/clt-inventory` on the Montavilla CLT site that shows every CLT in the inventory pipeline: name, location, website, and pipeline status. Acts as a transparency surface for the research work.

## Non-goals

- No emails displayed (internal only).
- No CSV download button.
- No map rendering (separate page at `/clt-map`).
- No server-side pagination (client-side filter + sort is sufficient for ~300–400 rows).

## Architecture

**Build-time data pipeline.**

1. New Node script `scripts/dump-clt-inventory.mjs` connects to Neon via `DATABASE_URL`, selects
   `SELECT id, name, city, state, url, status FROM inv_clts ORDER BY state, name` (no emails), and writes
   the rows plus a generated-at timestamp to `src/data/clt-inventory.json`.
2. `package.json` `build` script runs the dump before Astro: `"build": "node scripts/dump-clt-inventory.mjs && astro build"`.
3. `src/data/clt-inventory.json` is gitignored (regenerated each deploy).

**Page.**

- `src/pages/clt-inventory.astro` with `export const prerender = true`, imports the JSON at build time.
- Matches existing `clt-map.astro` layout: forest hero, Nav, Footer, consistent palette and typography.

## Page structure

```
Hero (forest bg, ochre accent)
  Eyebrow: INVENTORY
  H1: "U.S. Community Land Trusts"
  Subhead: count + last updated
  Back link

Search bar (single input, filters on name + city + state, case-insensitive substring)

Table
  Columns: Name | Location | Website | Status
  Click header to sort asc/desc (default: Name asc)
  Row count footer reflects current filter state
```

## Data contract

`src/data/clt-inventory.json`:

```json
{
  "generated_at": "2026-04-17T13:42:00Z",
  "rows": [
    { "id": "proud-ground", "name": "Proud Ground", "city": "Portland", "state": "OR", "url": "https://www.proudground.org", "status": "extracted" },
    ...
  ]
}
```

## Status pill mapping

- `extracted`, `url_found` → green (`var(--sage)` or similar)
- `discovered` → ochre (pending discovery)
- `url_not_found`, `rescue_failed`, `crawl_failed` → muted gray

Displayed text is human-friendly: "live", "pending", "no site found".

## Interactivity

Single inline `<script>` in the Astro page. No frameworks, no external JS deps.

- Search: `<input type="search">` → event listener filters visible `<tr>` elements via `.hidden` toggle.
- Sort: each sortable `<th>` has `data-sort="<col>"` and `aria-sort`. Click toggles asc/desc, reorders rows in place.

## Nav integration

Add `<a href="/clt-inventory">Inventory</a>` to `src/components/Nav.astro`.

## Testing

This is a static page over a static JSON dump. Testing is manual:
- Run the dump script against live Neon; confirm the JSON has the expected row count.
- `astro dev`, visit `/clt-inventory`, exercise filter + sort.
- Spot-check that status pills colour correctly and website links open in new tabs.

No unit tests — the page is declarative Astro + ~40 lines of vanilla JS; a browser render test is the only meaningful verification.

## Out-of-scope follow-ups

- CSV export button.
- Role / email display for logged-in admins (would need auth surface).
- Geographic grouping view (map already lives at `/clt-map`).
