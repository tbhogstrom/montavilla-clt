# CLT Inventory Pipeline — Design

**Date:** 2026-04-16
**Status:** Approved (design)
**Owner:** tfalcon

## Goal

Build a Python/Jupyter pipeline that inventories ~300 US Community Land Trusts, discovers their websites, crawls the relevant pages, stores HTML locally, extracts contact emails, and writes the expanded public dataset back into `src/data/clts.json` so the site map reflects the full inventory.

The 33 hand-curated CLTs already in `src/data/clts.json` are preserved verbatim; everything new is additive. Email addresses are kept in the database for internal outreach use only and are never written to the public site.

## Non-goals (v1)

- Automated classification of `axes` / `focus` from page content. New entries get placeholder values flagged for manual review.
- Staff or board name extraction.
- Phone number or postal address extraction.
- Frontend changes. The site already reads `clts.json`; the expanded data shows up automatically when the export stage runs.

## Architecture

```
pipeline/
  __init__.py
  db.py            # psycopg connection, schema bootstrap, helpers
  seeds.py         # directory scrapers (Grounded Solutions, Center for CLT Innovation)
  serpapi.py       # thin SerpAPI wrapper backed by inv_serpapi_cache
  discover.py      # given a CLT name+state, find its URL via SerpAPI
  crawler.py       # fetch homepage + contact/about pages; rescue pass
  extractor.py     # pull emails out of stored HTML
  export.py        # rewrite src/data/clts.json from inv_clts (no emails)

notebooks/
  run_pipeline.ipynb   # thin orchestrator; one cell per stage

data/                  # gitignored
  html/<clt_id>/<page_kind>-<sha256[:8]>.html
  cache/serpapi/        # optional on-disk mirror of inv_serpapi_cache
```

The orchestrator notebook is the linear walkthrough; the modules are the reusable code. Library functions are import-and-call-from-cell so the kernel never holds stale logic after edits.

## Execution shape

**Stage-batched, not per-CLT-end-to-end.** All CLTs flow through stage 1, then stage 2, etc. This makes:

- each stage independently resumable (re-running stage 5 after improving the email regex doesn't re-crawl);
- intermediate state inspectable in Postgres between stages;
- failures isolated to one stage at a time.

Pipeline state is stored exclusively in `inv_clts.status`. Every stage's first action is `SELECT id FROM inv_clts WHERE status = '<previous_stage>'`.

## Sources

**Seed (no SerpAPI):**
- Grounded Solutions Network member directory — closest thing to a canonical US CLT list.
- Center for CLT & Cooperative Innovation — overlaps GSN but catches rural/agricultural trusts GSN underrepresents.
- Existing `src/data/clts.json` — seeded with `source='existing'` so we never lose what we already have.

**Backfill (SerpAPI):** state-by-state sweep `"community land trust" "<state>"` for any CLT not in the directories.

**Discovery (SerpAPI):** for each named CLT lacking a URL, `"<CLT name>" "<city>" <state> community land trust`.

**Rescue (SerpAPI):** for each CLT whose site is dead/parked/404, broader query `"<CLT name>" <city> <state>` to find a moved or successor URL.

## Database schema (Neon, `inv_` prefix on shared DB)

```sql
CREATE TABLE inv_clts (
  id              text PRIMARY KEY,         -- slug, e.g. "proud-ground"
  name            text NOT NULL,
  city            text,
  state           text,                     -- 2-letter
  url             text,                     -- canonical website
  source          text,                     -- 'grounded-solutions',
                                            -- 'center-clt-innovation',
                                            -- 'serpapi-sweep', 'existing'
  status          text NOT NULL,            -- 'discovered' | 'url_found'
                                            -- | 'url_not_found' | 'crawled'
                                            -- | 'crawl_failed' | 'rescued'
                                            -- | 'extracted'
  notes           text,
  first_seen_at   timestamptz NOT NULL DEFAULT now(),
  updated_at      timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX inv_clts_status_idx ON inv_clts (status);
CREATE INDEX inv_clts_state_idx  ON inv_clts (state);

CREATE TABLE inv_pages (
  id              bigserial PRIMARY KEY,
  clt_id          text NOT NULL REFERENCES inv_clts(id) ON DELETE CASCADE,
  url             text NOT NULL,
  page_kind       text NOT NULL,            -- 'home' | 'contact' | 'about'
                                            -- | 'staff' | 'team' | 'board'
  http_status     int,
  fetched_at      timestamptz NOT NULL DEFAULT now(),
  html_path       text,                     -- relative path under data/html/
  content_hash    text,                     -- sha256 of body
  error           text,
  UNIQUE (clt_id, url)
);
CREATE INDEX inv_pages_clt_idx ON inv_pages (clt_id);

CREATE TABLE inv_emails (
  id              bigserial PRIMARY KEY,
  clt_id          text NOT NULL REFERENCES inv_clts(id) ON DELETE CASCADE,
  page_id         bigint NOT NULL REFERENCES inv_pages(id) ON DELETE CASCADE,
  email           text NOT NULL,            -- lowercased, normalized
  source          text NOT NULL,            -- 'mailto' | 'text' | 'deobfuscated'
  context         text,                     -- ~200-char snippet around match
  extracted_at    timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX inv_emails_clt_idx   ON inv_emails (clt_id);
CREATE INDEX inv_emails_email_idx ON inv_emails (email);

CREATE TABLE inv_serpapi_cache (
  query_hash      text PRIMARY KEY,         -- sha256 of normalized query
  query           text NOT NULL,
  response_json   jsonb NOT NULL,
  fetched_at      timestamptz NOT NULL DEFAULT now()
);
```

`inv_serpapi_cache` is the most important cost-saving piece — re-runs hit cache and never burn credits.

## Stages

### Stage 1 — Seed (`pipeline/seeds.py`)

Scrape the two directory pages, plus seed from the existing `clts.json`. Upserts into `inv_clts` keyed by slugified name. Status: `discovered` (or `url_found` if the directory exposed a URL).

### Stage 2 — Discover websites (`pipeline/discover.py`)

For each CLT where `url IS NULL`:

- SerpAPI query: `"<CLT name>" "<city>" <state> community land trust`.
- Pick the top organic result whose domain (a) contains a token from the CLT name, (b) is not a social platform (facebook, linkedin, instagram, x.com, twitter, youtube), (c) is not a news site, (d) is not a government domain unless the org name explicitly references the agency.
- On confident match: set `url`, `status='url_found'`. Otherwise `status='url_not_found'`.

Every SerpAPI response is cached in `inv_serpapi_cache`.

### Stage 3 — Crawl (`pipeline/crawler.py`)

For each CLT where `status='url_found'`:

1. Fetch homepage with `requests`. User-Agent: `MontavillaCLT-Inventory/1.0 (research; tfalcon@sfwconstruction.com)`. 20s connect/read timeout. Follow redirects.
2. Check `robots.txt` via `urllib.robotparser`; respect `Disallow`.
3. Parse with BeautifulSoup; find same-domain links whose href or visible text matches `contact|about|staff|team|board` (case-insensitive). Cap at 8 unique contact-like links per site (the homepage is always fetched in addition).
4. Fetch matched links with the same timeout/UA; classify each into `page_kind`.
5. Write raw HTML to `data/html/<clt_id>/<page_kind>-<sha256[:8]>.html`. Insert one `inv_pages` row per fetch (success or failure — failures get `error` populated).
6. 1.5s minimum delay between requests to the same host (in-memory dict keyed by domain).
7. Transition CLT to `status='crawled'` on at least one successful fetch; `status='crawl_failed'` if every fetch failed.

### Stage 4 — Rescue (`pipeline/crawler.py`, separate entry point)

For each CLT where `status='crawl_failed'`:

- Broader SerpAPI query: `"<CLT name>" <city> <state>`.
- If a different plausible URL is returned (passes the same heuristics as stage 2), replace `url`, set `status='url_found'`, and re-run stage 3 on just that CLT. The audit trail lives in `inv_pages`: the original failed rows are preserved, and a new successful row points at the new URL.
- Otherwise leave as `crawl_failed`.

### Stage 5 — Extract emails (`pipeline/extractor.py`)

For each CLT where `status='crawled'`, walk every `inv_pages` row's HTML:

- `mailto:` links → `source='mailto'`.
- Visible-text regex (RFC-flavored email pattern, anchored to word boundaries) → `source='text'`.
- Deobfuscation patterns: `name [at] domain [dot] org`, `name (at) domain (dot) org`, `name AT domain DOT org` → `source='deobfuscated'`.
- Normalize: lowercase, strip trailing punctuation.
- Reject by domain blocklist: `example.com`, `sentry.io`, `wixpress.com`, `squarespace.com`, `wordpress.com`, common image-CDN/asset hosts.
- Capture ~200-char context snippet around each match.
- One `inv_emails` row per occurrence (provenance preserved). Dedup by `(clt_id, email)` happens at outreach-export time, not at insert.

Set CLT `status='extracted'`.

### Export (`pipeline/export.py`)

Rebuilds `src/data/clts.json` from `inv_clts`. Emails are NOT included — `inv_emails` is internal-only.

1. `SELECT id, name, city, state, url, notes FROM inv_clts WHERE url IS NOT NULL`.
2. Compose `location` as `"<city>, <state>"` to match existing schema.
3. Read existing `clts.json`; for any matching `id`, preserve `founded`, `focus`, `axes`, `scale`, `notes` verbatim. For new entries, default:
   - `founded`: `null`
   - `focus`: `["housing"]`
   - `axes`: `{ "housing": 90, "agriculture": 5, "commercial": 5 }`
   - `scale`: `null`
4. Write sorted by state then name for stable diffs.
5. Print summary: `existing: 33 (preserved), new: N, total: M, skipped (no url): K`.

Export is its own opt-in cell in the notebook — it's the only stage that writes back into the site repo.

## Politeness, error handling, resumability

**Politeness:**
- Single descriptive User-Agent (above) — identifies us so site owners can contact if they object.
- 1.5s per-domain throttle.
- `robots.txt` honored; disallowed pages skipped with `error='robots-disallowed'`.
- 20s timeout. One retry on transient errors (5xx, ConnectionError) with 5s backoff. No retry on 4xx.
- No concurrency in v1. Sequential is plenty for ~300 sites and avoids hammering small org servers.

**Error handling philosophy:**
- Errors are data, not exceptions to escape. Every failure mode lands in a column (`inv_pages.error`, `inv_clts.status`) so the notebook can surface them with a SELECT instead of a re-run.
- The crawler never raises out of a per-CLT loop — it catches, logs, sets status, moves on.
- SerpAPI failures (rate limit, network) raise — a budget/network problem should stop the run, not silently degrade.

**Resumability:**
- Every stage is "find work, do work" — `SELECT id FROM inv_clts WHERE status = '<previous_stage>'`. Re-running a stage is a no-op for already-completed CLTs.
- Force re-crawl: `UPDATE inv_clts SET status = 'url_found' WHERE id = '...'`.
- HTML files are content-addressed (`<page_kind>-<sha256[:8]>.html`) so re-crawls keep history.
- `inv_serpapi_cache` makes re-runs free in credits.

**Notebook UX:**
- One cell per stage. Each prints `N CLTs pending → processing → M succeeded, K failed`.
- Final diagnostics cell: `status` distribution, top 10 error messages, sample of CLTs with no email found.

## Configuration

`.env` (gitignored):
- `DATABASE_URL` — Neon connection string (already used by site).
- `SERPAPI_KEY` — SerpAPI credential.

Pipeline reads `.env` via `python-dotenv`.

`data/` directory added to `.gitignore`.

## Dependencies (pinned in `pipeline/requirements.txt`)

- `requests`
- `beautifulsoup4`
- `psycopg[binary]` (v3)
- `python-dotenv`
- `jupyterlab`
- Direct SerpAPI HTTP via `requests` (no SDK dependency)

## SerpAPI budget estimate

- Directory scrape: 0 credits.
- State-by-state sweep (50 states × 2 queries): ~100 credits.
- Discovery for ~300 names: ~300-600 credits (1-2 each, cached on retry).
- Rescue pass for crawl failures: ~50-100 credits.

Realistic total: **500-1,000 credits** for a clean run. Re-runs are free thanks to `inv_serpapi_cache`.

## Out-of-scope follow-ups (separate projects later)

- LLM-based classification to fill `axes` and `focus` from crawled HTML.
- Staff/board name and role extraction.
- Phone numbers, addresses, social handles.
- Public outreach UI (currently the export only feeds the map; outreach is a separate workflow).
