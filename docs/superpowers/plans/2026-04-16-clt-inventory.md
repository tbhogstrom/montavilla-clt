# CLT Inventory Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Python/Jupyter pipeline that inventories ~300 US Community Land Trusts, discovers their websites via SerpAPI, crawls homepage + contact-like pages, extracts emails, and exports the public-safe dataset back to `src/data/clts.json`.

**Architecture:** Stage-batched pipeline. Library code in `pipeline/` Python modules; thin orchestrator notebook in `notebooks/run_pipeline.ipynb`. State machine driven by `inv_clts.status` in Neon (shared DB with `inv_` prefix). Raw HTML stored on local disk under `data/html/`. SerpAPI responses cached in Neon to make re-runs free.

**Tech Stack:** Python 3.11+, `requests`, `beautifulsoup4`, `psycopg[binary]` v3, `python-dotenv`, `jupyterlab`, `pytest`, `responses` (HTTP mocking).

**Reference:** [`docs/superpowers/specs/2026-04-16-clt-inventory-design.md`](../specs/2026-04-16-clt-inventory-design.md)

**File map:**
```
pipeline/
  __init__.py
  config.py        # env loading, paths
  db.py            # psycopg connection, schema bootstrap
  http.py          # throttled session, robots.txt
  serpapi.py       # SerpAPI client backed by inv_serpapi_cache
  discover.py      # name → URL via SerpAPI + heuristics
  links.py         # contact-like link finder + page_kind classifier
  crawler.py       # crawl + rescue
  extractor.py     # email extraction (mailto, regex, deobfuscation)
  seeds.py         # directory scrapers + existing-JSON seeder + state sweep
  export.py        # rebuild src/data/clts.json from inv_clts
requirements.txt
README.md          # only if user asks; spec doc + this plan suffice
tests/
  conftest.py
  test_config.py
  test_http.py
  test_robots.py
  test_serpapi.py
  test_discover.py
  test_links.py
  test_crawler.py
  test_extractor.py
  test_export.py
  test_seeds.py
  fixtures/
    sample_homepage.html
    sample_contact.html
    grounded_solutions.html
    center_clt.html
notebooks/
  run_pipeline.ipynb
```

**Important Windows note:** the user runs git-bash. Use forward-slash paths everywhere. The venv activation path is `.venv/Scripts/activate` (not `.venv/bin/activate`).

---

## Task 1: Project bootstrap

**Files:**
- Create: `pipeline/__init__.py`
- Create: `requirements.txt`
- Create: `tests/__init__.py`
- Create: `tests/conftest.py`
- Create: `notebooks/.gitkeep`
- Modify: `.gitignore`

- [ ] **Step 1: Add `data/`, `.venv/`, and pytest cache to `.gitignore`**

The current `.gitignore` is:
```
node_modules/
dist/
.astro/
.env
.vercel/
*.DS_Store
```

Replace it with:
```
node_modules/
dist/
.astro/
.env
.vercel/
*.DS_Store

# Python
.venv/
__pycache__/
*.pyc
.pytest_cache/
.ipynb_checkpoints/

# CLT inventory pipeline raw data (local-only)
data/
```

- [ ] **Step 2: Create `requirements.txt`**

```
requests==2.32.3
beautifulsoup4==4.12.3
lxml==5.3.0
psycopg[binary]==3.2.3
python-dotenv==1.0.1
jupyterlab==4.3.4
pytest==8.3.4
responses==0.25.3
freezegun==1.5.1
```

- [ ] **Step 3: Create `pipeline/__init__.py` (empty marker file)**

```python
```

- [ ] **Step 4: Create `tests/__init__.py` (empty marker file)**

```python
```

- [ ] **Step 5: Create `tests/conftest.py`**

```python
"""Pytest config — make the `pipeline` package importable from tests."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
```

- [ ] **Step 6: Create `notebooks/.gitkeep` (empty)**

```
```

- [ ] **Step 7: Set up venv and install deps**

Run:
```bash
cd C:/Users/tfalcon/montavilla-clt
python -m venv .venv
source .venv/Scripts/activate
pip install -r requirements.txt
```

Expected: clean install, no errors. `pip list` should show all packages above.

- [ ] **Step 8: Smoke test pytest discovery**

Run:
```bash
source .venv/Scripts/activate
python -m pytest --collect-only
```

Expected: `0 tests collected` (no tests written yet, but no errors).

- [ ] **Step 9: Commit**

```bash
git add .gitignore requirements.txt pipeline/__init__.py tests/__init__.py tests/conftest.py notebooks/.gitkeep
git commit -m "Bootstrap CLT inventory Python pipeline skeleton"
```

---

## Task 2: Config module

**Files:**
- Create: `pipeline/config.py`
- Create: `tests/test_config.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_config.py`:
```python
"""Tests for pipeline.config."""
from pathlib import Path
from unittest import mock

from pipeline import config


def test_paths_are_absolute_and_under_repo_root():
    assert config.REPO_ROOT.is_absolute()
    assert config.DATA_DIR == config.REPO_ROOT / "data"
    assert config.HTML_DIR == config.REPO_ROOT / "data" / "html"
    assert config.SITE_CLTS_JSON == config.REPO_ROOT / "src" / "data" / "clts.json"


def test_load_env_returns_required_vars(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text("DATABASE_URL=postgres://x\nSERPAPI_KEY=abc123\n")
    monkeypatch.setattr(config, "ENV_PATH", env_file)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("SERPAPI_KEY", raising=False)

    env = config.load_env()
    assert env["DATABASE_URL"] == "postgres://x"
    assert env["SERPAPI_KEY"] == "abc123"


def test_load_env_raises_when_required_missing(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text("DATABASE_URL=postgres://x\n")  # SERPAPI_KEY missing
    monkeypatch.setattr(config, "ENV_PATH", env_file)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("SERPAPI_KEY", raising=False)

    try:
        config.load_env()
    except RuntimeError as exc:
        assert "SERPAPI_KEY" in str(exc)
    else:
        raise AssertionError("expected RuntimeError")
```

- [ ] **Step 2: Run tests to verify they fail**

Run:
```bash
source .venv/Scripts/activate
python -m pytest tests/test_config.py -v
```

Expected: ImportError or failure on `from pipeline import config`.

- [ ] **Step 3: Implement `pipeline/config.py`**

```python
"""Config: paths and environment loading for the CLT inventory pipeline."""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import dotenv_values

REPO_ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = REPO_ROOT / ".env"
DATA_DIR = REPO_ROOT / "data"
HTML_DIR = DATA_DIR / "html"
SITE_CLTS_JSON = REPO_ROOT / "src" / "data" / "clts.json"

REQUIRED_ENV = ("DATABASE_URL", "SERPAPI_KEY")

USER_AGENT = (
    "MontavillaCLT-Inventory/1.0 "
    "(research; tfalcon@sfwconstruction.com)"
)
HTTP_TIMEOUT = 20  # seconds, connect/read
PER_DOMAIN_DELAY = 1.5  # seconds between requests to the same host
MAX_CONTACT_LINKS = 8


def load_env() -> dict[str, str]:
    """Read .env and the process environment; return required vars or raise."""
    file_env = dotenv_values(ENV_PATH) if ENV_PATH.exists() else {}
    merged = {**file_env, **{k: os.environ[k] for k in os.environ if k in REQUIRED_ENV}}
    missing = [k for k in REQUIRED_ENV if not merged.get(k)]
    if missing:
        raise RuntimeError(f"Missing required env vars: {', '.join(missing)}")
    return {k: merged[k] for k in REQUIRED_ENV}
```

- [ ] **Step 4: Run tests to verify they pass**

Run:
```bash
python -m pytest tests/test_config.py -v
```

Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add pipeline/config.py tests/test_config.py
git commit -m "Add config module with env loading and pipeline constants"
```

---

## Task 3: DB connection + schema bootstrap

**Files:**
- Create: `pipeline/db.py`
- Create: `tests/test_db_smoke.py`

- [ ] **Step 1: Implement `pipeline/db.py`**

Schema bootstrap is mostly glue against Postgres-specific syntax (jsonb, bigserial), so we don't unit-test SQL — we smoke-test against the real Neon DB. The connection helper is a thin wrapper.

```python
"""Postgres connection + schema bootstrap for inv_* tables."""
from __future__ import annotations

import contextlib
from typing import Iterator

import psycopg

from pipeline.config import load_env

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS inv_clts (
  id              text PRIMARY KEY,
  name            text NOT NULL,
  city            text,
  state           text,
  url             text,
  source          text,
  status          text NOT NULL,
  notes           text,
  first_seen_at   timestamptz NOT NULL DEFAULT now(),
  updated_at      timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS inv_clts_status_idx ON inv_clts (status);
CREATE INDEX IF NOT EXISTS inv_clts_state_idx  ON inv_clts (state);

CREATE TABLE IF NOT EXISTS inv_pages (
  id              bigserial PRIMARY KEY,
  clt_id          text NOT NULL REFERENCES inv_clts(id) ON DELETE CASCADE,
  url             text NOT NULL,
  page_kind       text NOT NULL,
  http_status     int,
  fetched_at      timestamptz NOT NULL DEFAULT now(),
  html_path       text,
  content_hash    text,
  error           text,
  UNIQUE (clt_id, url)
);
CREATE INDEX IF NOT EXISTS inv_pages_clt_idx ON inv_pages (clt_id);

CREATE TABLE IF NOT EXISTS inv_emails (
  id              bigserial PRIMARY KEY,
  clt_id          text NOT NULL REFERENCES inv_clts(id) ON DELETE CASCADE,
  page_id         bigint NOT NULL REFERENCES inv_pages(id) ON DELETE CASCADE,
  email           text NOT NULL,
  source          text NOT NULL,
  context         text,
  extracted_at    timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS inv_emails_clt_idx   ON inv_emails (clt_id);
CREATE INDEX IF NOT EXISTS inv_emails_email_idx ON inv_emails (email);

CREATE TABLE IF NOT EXISTS inv_serpapi_cache (
  query_hash      text PRIMARY KEY,
  query           text NOT NULL,
  response_json   jsonb NOT NULL,
  fetched_at      timestamptz NOT NULL DEFAULT now()
);
"""


@contextlib.contextmanager
def connect() -> Iterator[psycopg.Connection]:
    """Yield a psycopg connection using DATABASE_URL from .env."""
    env = load_env()
    conn = psycopg.connect(env["DATABASE_URL"])
    try:
        yield conn
    finally:
        conn.close()


def bootstrap_schema() -> None:
    """Idempotently create inv_* tables and indexes."""
    with connect() as conn, conn.cursor() as cur:
        cur.execute(SCHEMA_SQL)
        conn.commit()
```

- [ ] **Step 2: Write a smoke test that runs against the real Neon DB**

Create `tests/test_db_smoke.py`:
```python
"""Smoke test: bootstrap schema, insert a temp row, read it back, clean up.

Skipped when DATABASE_URL is not configured. This is the only test that
hits a real database.
"""
import os
from pathlib import Path

import pytest
from dotenv import dotenv_values

from pipeline import db
from pipeline.config import ENV_PATH

env = {**dotenv_values(ENV_PATH), **os.environ} if ENV_PATH.exists() else dict(os.environ)
DB_URL = env.get("DATABASE_URL")

pytestmark = pytest.mark.skipif(
    not DB_URL, reason="DATABASE_URL not set; skipping live-DB smoke test"
)


def test_bootstrap_and_roundtrip():
    db.bootstrap_schema()
    with db.connect() as conn, conn.cursor() as cur:
        cur.execute(
            "INSERT INTO inv_clts (id, name, status, source) "
            "VALUES (%s, %s, %s, %s) ON CONFLICT (id) DO NOTHING",
            ("__smoketest__", "Smoke Test CLT", "discovered", "manual"),
        )
        cur.execute("SELECT name FROM inv_clts WHERE id = %s", ("__smoketest__",))
        row = cur.fetchone()
        assert row is not None
        assert row[0] == "Smoke Test CLT"
        cur.execute("DELETE FROM inv_clts WHERE id = %s", ("__smoketest__",))
        conn.commit()
```

- [ ] **Step 3: Run the smoke test**

The user must have `DATABASE_URL` set in `.env` for this to run. If not, ask them to fill it in before continuing.

```bash
source .venv/Scripts/activate
python -m pytest tests/test_db_smoke.py -v
```

Expected: `1 passed` (or `1 skipped` if DATABASE_URL is not set — in which case STOP and ask the user to set it before proceeding).

- [ ] **Step 4: Commit**

```bash
git add pipeline/db.py tests/test_db_smoke.py
git commit -m "Add Neon connection helper and inv_* schema bootstrap"
```

---

## Task 4: Throttled HTTP session

**Files:**
- Create: `pipeline/http.py`
- Create: `tests/test_http.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_http.py`:
```python
"""Tests for pipeline.http.ThrottledSession."""
import time
from unittest import mock

import responses

from pipeline.http import ThrottledSession, USER_AGENT


@responses.activate
def test_get_sets_user_agent_and_returns_response():
    responses.add(responses.GET, "https://example.org/", body="hello", status=200)
    session = ThrottledSession()
    resp = session.get("https://example.org/")
    assert resp.status_code == 200
    assert resp.text == "hello"
    assert responses.calls[0].request.headers["User-Agent"] == USER_AGENT


@responses.activate
def test_get_throttles_repeated_requests_to_same_host():
    responses.add(responses.GET, "https://example.org/a", body="a", status=200)
    responses.add(responses.GET, "https://example.org/b", body="b", status=200)
    sleeps: list[float] = []
    session = ThrottledSession(per_domain_delay=0.5, sleep=sleeps.append)
    session.get("https://example.org/a")
    session.get("https://example.org/b")
    # First call has no sleep; second must sleep ~0.5s minus elapsed.
    assert len(sleeps) == 1
    assert 0 < sleeps[0] <= 0.5


@responses.activate
def test_get_does_not_throttle_across_different_hosts():
    responses.add(responses.GET, "https://a.org/", body="a", status=200)
    responses.add(responses.GET, "https://b.org/", body="b", status=200)
    sleeps: list[float] = []
    session = ThrottledSession(per_domain_delay=0.5, sleep=sleeps.append)
    session.get("https://a.org/")
    session.get("https://b.org/")
    assert sleeps == []  # different hosts, no throttle


@responses.activate
def test_get_retries_once_on_5xx():
    responses.add(responses.GET, "https://example.org/", status=503)
    responses.add(responses.GET, "https://example.org/", body="ok", status=200)
    session = ThrottledSession(retry_backoff=0, sleep=lambda s: None)
    resp = session.get("https://example.org/")
    assert resp.status_code == 200
    assert len(responses.calls) == 2


@responses.activate
def test_get_does_not_retry_on_4xx():
    responses.add(responses.GET, "https://example.org/", status=404)
    session = ThrottledSession(retry_backoff=0, sleep=lambda s: None)
    resp = session.get("https://example.org/")
    assert resp.status_code == 404
    assert len(responses.calls) == 1
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
python -m pytest tests/test_http.py -v
```

Expected: ImportError on `from pipeline.http import ...`.

- [ ] **Step 3: Implement `pipeline/http.py`**

```python
"""Polite HTTP session: User-Agent, per-domain throttle, one retry on 5xx."""
from __future__ import annotations

import time
from typing import Callable
from urllib.parse import urlparse

import requests

from pipeline.config import USER_AGENT, HTTP_TIMEOUT, PER_DOMAIN_DELAY


class ThrottledSession:
    """A requests-backed session that throttles per-domain and retries 5xx once."""

    def __init__(
        self,
        per_domain_delay: float = PER_DOMAIN_DELAY,
        timeout: float = HTTP_TIMEOUT,
        retry_backoff: float = 5.0,
        sleep: Callable[[float], None] = time.sleep,
        clock: Callable[[], float] = time.monotonic,
    ):
        self._per_domain_delay = per_domain_delay
        self._timeout = timeout
        self._retry_backoff = retry_backoff
        self._sleep = sleep
        self._clock = clock
        self._last_hit: dict[str, float] = {}
        self._session = requests.Session()
        self._session.headers["User-Agent"] = USER_AGENT

    def _throttle(self, host: str) -> None:
        last = self._last_hit.get(host)
        now = self._clock()
        if last is not None:
            elapsed = now - last
            if elapsed < self._per_domain_delay:
                self._sleep(self._per_domain_delay - elapsed)
        self._last_hit[host] = self._clock()

    def get(self, url: str) -> requests.Response:
        host = urlparse(url).netloc.lower()
        self._throttle(host)
        try:
            resp = self._session.get(url, timeout=self._timeout, allow_redirects=True)
        except requests.ConnectionError:
            self._sleep(self._retry_backoff)
            resp = self._session.get(url, timeout=self._timeout, allow_redirects=True)
            return resp
        if resp.status_code >= 500:
            self._sleep(self._retry_backoff)
            resp = self._session.get(url, timeout=self._timeout, allow_redirects=True)
        return resp
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
python -m pytest tests/test_http.py -v
```

Expected: 5 passed.

- [ ] **Step 5: Commit**

```bash
git add pipeline/http.py tests/test_http.py
git commit -m "Add throttled HTTP session with per-domain politeness and 5xx retry"
```

---

## Task 5: robots.txt checker

**Files:**
- Create: `pipeline/robots.py`
- Create: `tests/test_robots.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_robots.py`:
```python
"""Tests for pipeline.robots.RobotsCache."""
from unittest import mock

import responses

from pipeline.robots import RobotsCache
from pipeline.config import USER_AGENT


@responses.activate
def test_allows_when_robots_missing():
    responses.add(responses.GET, "https://example.org/robots.txt", status=404)
    cache = RobotsCache()
    assert cache.allowed("https://example.org/contact")


@responses.activate
def test_disallowed_path_blocked():
    body = "User-agent: *\nDisallow: /private/\n"
    responses.add(responses.GET, "https://example.org/robots.txt", body=body, status=200)
    cache = RobotsCache()
    assert not cache.allowed("https://example.org/private/secret")
    assert cache.allowed("https://example.org/contact")


@responses.activate
def test_robots_fetched_once_per_host():
    responses.add(responses.GET, "https://example.org/robots.txt", body="", status=200)
    cache = RobotsCache()
    cache.allowed("https://example.org/a")
    cache.allowed("https://example.org/b")
    assert len(responses.calls) == 1


@responses.activate
def test_network_error_treated_as_allowed():
    responses.add(responses.GET, "https://example.org/robots.txt", body=ConnectionError("boom"))
    cache = RobotsCache()
    assert cache.allowed("https://example.org/anything")
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
python -m pytest tests/test_robots.py -v
```

Expected: ImportError.

- [ ] **Step 3: Implement `pipeline/robots.py`**

```python
"""Per-host robots.txt cache. Fetched once per host; failures fail open (allow)."""
from __future__ import annotations

from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import requests

from pipeline.config import USER_AGENT, HTTP_TIMEOUT


class RobotsCache:
    def __init__(self):
        self._parsers: dict[str, RobotFileParser] = {}

    def _load(self, host_url: str) -> RobotFileParser:
        rp = RobotFileParser()
        try:
            resp = requests.get(
                f"{host_url}/robots.txt",
                headers={"User-Agent": USER_AGENT},
                timeout=HTTP_TIMEOUT,
            )
            if resp.status_code == 200:
                rp.parse(resp.text.splitlines())
            else:
                rp.parse([])  # treat as fully open
        except requests.RequestException:
            rp.parse([])
        return rp

    def allowed(self, url: str) -> bool:
        parsed = urlparse(url)
        host_url = f"{parsed.scheme}://{parsed.netloc}"
        if host_url not in self._parsers:
            self._parsers[host_url] = self._load(host_url)
        return self._parsers[host_url].can_fetch(USER_AGENT, url)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
python -m pytest tests/test_robots.py -v
```

Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add pipeline/robots.py tests/test_robots.py
git commit -m "Add cached robots.txt checker (fail-open on network error)"
```

---

## Task 6: SerpAPI cached client

**Files:**
- Create: `pipeline/serpapi.py`
- Create: `tests/test_serpapi.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_serpapi.py`. We mock both the HTTP layer and the DB layer (the DB layer is a tiny interface we'll define in serpapi.py).

```python
"""Tests for pipeline.serpapi.SerpApiClient."""
import json
from unittest import mock

import responses

from pipeline.serpapi import SerpApiClient, normalized_query_hash, ENDPOINT


class FakeCache:
    def __init__(self):
        self.store: dict[str, dict] = {}

    def get(self, query_hash: str):
        return self.store.get(query_hash)

    def put(self, query_hash: str, query: str, response: dict):
        self.store[query_hash] = response


def test_normalized_query_hash_is_stable():
    h1 = normalized_query_hash("  Hello  WORLD  ")
    h2 = normalized_query_hash("hello world")
    assert h1 == h2
    assert len(h1) == 64  # sha256 hex


@responses.activate
def test_search_caches_response_on_first_call():
    payload = {"organic_results": [{"link": "https://example.org/"}]}
    responses.add(responses.GET, ENDPOINT, json=payload, status=200)
    cache = FakeCache()
    client = SerpApiClient(api_key="KEY", cache=cache)

    result = client.search("community land trust portland or")
    assert result == payload
    assert len(cache.store) == 1
    assert len(responses.calls) == 1


@responses.activate
def test_search_returns_cached_without_http():
    cache = FakeCache()
    cache.put(normalized_query_hash("foo"), "foo", {"cached": True})
    client = SerpApiClient(api_key="KEY", cache=cache)
    result = client.search("foo")
    assert result == {"cached": True}
    assert len(responses.calls) == 0


@responses.activate
def test_search_raises_on_non_200():
    responses.add(responses.GET, ENDPOINT, status=500, body="boom")
    cache = FakeCache()
    client = SerpApiClient(api_key="KEY", cache=cache)
    try:
        client.search("anything")
    except RuntimeError as exc:
        assert "500" in str(exc)
    else:
        raise AssertionError("expected RuntimeError")


@responses.activate
def test_search_passes_query_and_api_key():
    payload = {"organic_results": []}
    responses.add(responses.GET, ENDPOINT, json=payload, status=200)
    cache = FakeCache()
    client = SerpApiClient(api_key="MYKEY", cache=cache)
    client.search("something")
    sent = responses.calls[0].request.url
    assert "q=something" in sent
    assert "api_key=MYKEY" in sent
    assert "engine=google" in sent
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
python -m pytest tests/test_serpapi.py -v
```

Expected: ImportError.

- [ ] **Step 3: Implement `pipeline/serpapi.py`**

```python
"""SerpAPI client with a pluggable cache backend.

The cache interface is two methods: get(hash) -> response or None; and
put(hash, query, response). Production cache backed by inv_serpapi_cache
in Postgres; tests use an in-memory dict.
"""
from __future__ import annotations

import hashlib
from typing import Protocol

import requests

from pipeline.config import HTTP_TIMEOUT, USER_AGENT

ENDPOINT = "https://serpapi.com/search.json"


class Cache(Protocol):
    def get(self, query_hash: str) -> dict | None: ...
    def put(self, query_hash: str, query: str, response: dict) -> None: ...


def normalized_query_hash(query: str) -> str:
    norm = " ".join(query.lower().split())
    return hashlib.sha256(norm.encode("utf-8")).hexdigest()


class SerpApiClient:
    def __init__(self, api_key: str, cache: Cache):
        self._api_key = api_key
        self._cache = cache

    def search(self, query: str, *, location: str | None = None) -> dict:
        h = normalized_query_hash(query if location is None else f"{query}|loc={location}")
        cached = self._cache.get(h)
        if cached is not None:
            return cached
        params = {
            "engine": "google",
            "q": query,
            "api_key": self._api_key,
            "num": 10,
        }
        if location is not None:
            params["location"] = location
        resp = requests.get(
            ENDPOINT,
            params=params,
            headers={"User-Agent": USER_AGENT},
            timeout=HTTP_TIMEOUT,
        )
        if resp.status_code != 200:
            raise RuntimeError(f"SerpAPI returned {resp.status_code}: {resp.text[:200]}")
        data = resp.json()
        self._cache.put(h, query, data)
        return data
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
python -m pytest tests/test_serpapi.py -v
```

Expected: 5 passed.

- [ ] **Step 5: Add the Postgres-backed cache implementation**

Append to `pipeline/serpapi.py`:
```python
import json

from pipeline.db import connect


class PostgresCache:
    """Cache backed by inv_serpapi_cache (used in production runs)."""

    def get(self, query_hash: str) -> dict | None:
        with connect() as conn, conn.cursor() as cur:
            cur.execute(
                "SELECT response_json FROM inv_serpapi_cache WHERE query_hash = %s",
                (query_hash,),
            )
            row = cur.fetchone()
            return row[0] if row else None

    def put(self, query_hash: str, query: str, response: dict) -> None:
        with connect() as conn, conn.cursor() as cur:
            cur.execute(
                "INSERT INTO inv_serpapi_cache (query_hash, query, response_json) "
                "VALUES (%s, %s, %s::jsonb) ON CONFLICT (query_hash) DO NOTHING",
                (query_hash, query, json.dumps(response)),
            )
            conn.commit()
```

- [ ] **Step 6: Commit**

```bash
git add pipeline/serpapi.py tests/test_serpapi.py
git commit -m "Add SerpAPI client with pluggable cache (in-memory + Postgres)"
```

---

## Task 7: Link finder + page-kind classifier

**Files:**
- Create: `pipeline/links.py`
- Create: `tests/test_links.py`
- Create: `tests/fixtures/sample_homepage.html`

- [ ] **Step 1: Create the HTML fixture**

Create `tests/fixtures/sample_homepage.html`:
```html
<!doctype html>
<html><head><title>Sample CLT</title></head><body>
  <nav>
    <a href="/">Home</a>
    <a href="/about-us">About Us</a>
    <a href="/our-team/">Our Team</a>
    <a href="/board-of-directors">Board</a>
    <a href="/contact-us">Contact</a>
    <a href="/get-involved/staff">Staff</a>
    <a href="https://facebook.com/sampleclt">Facebook</a>
    <a href="https://other-domain.org/about">External About</a>
    <a href="/news">News</a>
    <a href="mailto:info@sampleclt.org">info@sampleclt.org</a>
  </nav>
  <main>Welcome</main>
</body></html>
```

- [ ] **Step 2: Write the failing tests**

Create `tests/test_links.py`:
```python
"""Tests for pipeline.links."""
from pathlib import Path

from pipeline.links import find_contact_links, classify_page_kind

FIXTURE = Path(__file__).parent / "fixtures" / "sample_homepage.html"


def test_find_contact_links_returns_same_domain_only():
    html = FIXTURE.read_text()
    links = find_contact_links(html, base_url="https://sampleclt.org/")
    urls = [u for u, _ in links]
    assert "https://sampleclt.org/about-us" in urls
    assert "https://sampleclt.org/our-team/" in urls
    assert "https://sampleclt.org/board-of-directors" in urls
    assert "https://sampleclt.org/contact-us" in urls
    assert "https://sampleclt.org/get-involved/staff" in urls
    # external and unrelated:
    assert not any("facebook.com" in u for u in urls)
    assert not any("other-domain.org" in u for u in urls)
    assert not any(u.endswith("/news") for u in urls)


def test_find_contact_links_returns_classified_kinds():
    html = FIXTURE.read_text()
    links = dict(find_contact_links(html, base_url="https://sampleclt.org/"))
    assert links["https://sampleclt.org/about-us"] == "about"
    assert links["https://sampleclt.org/our-team/"] == "team"
    assert links["https://sampleclt.org/board-of-directors"] == "board"
    assert links["https://sampleclt.org/contact-us"] == "contact"
    assert links["https://sampleclt.org/get-involved/staff"] == "staff"


def test_find_contact_links_caps_at_max():
    # Build HTML with 20 contact-like links
    nav = "".join(f'<a href="/contact-{i}">Contact {i}</a>' for i in range(20))
    html = f"<html><body>{nav}</body></html>"
    links = find_contact_links(html, base_url="https://x.org/")
    assert len(links) == 8


def test_find_contact_links_dedupes_by_url():
    html = '<a href="/contact">a</a><a href="/contact">b</a>'
    links = find_contact_links(f"<html><body>{html}</body></html>", base_url="https://x.org/")
    assert len(links) == 1


def test_classify_page_kind_priority():
    assert classify_page_kind("/contact-us", "Contact") == "contact"
    assert classify_page_kind("/about", "About") == "about"
    assert classify_page_kind("/our-staff", "Staff") == "staff"
    assert classify_page_kind("/team", "The Team") == "team"
    assert classify_page_kind("/board", "Board") == "board"
    # ambiguous href falls back to link text
    assert classify_page_kind("/get-involved", "Contact") == "contact"
```

- [ ] **Step 3: Run tests to verify they fail**

```bash
python -m pytest tests/test_links.py -v
```

Expected: ImportError.

- [ ] **Step 4: Implement `pipeline/links.py`**

```python
"""Find and classify contact-like links on a CLT homepage."""
from __future__ import annotations

import re
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from pipeline.config import MAX_CONTACT_LINKS

# Order matters: most specific first wins on ties.
KIND_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("contact", re.compile(r"contact", re.I)),
    ("staff", re.compile(r"staff", re.I)),
    ("board", re.compile(r"board", re.I)),
    ("team", re.compile(r"team", re.I)),
    ("about", re.compile(r"about", re.I)),
]


def classify_page_kind(href: str, link_text: str) -> str | None:
    """Return one of contact/staff/board/team/about, or None if no match."""
    for kind, pat in KIND_PATTERNS:
        if pat.search(href):
            return kind
    for kind, pat in KIND_PATTERNS:
        if pat.search(link_text or ""):
            return kind
    return None


def _same_host(a: str, b: str) -> bool:
    return urlparse(a).netloc.lower() == urlparse(b).netloc.lower()


def find_contact_links(html: str, base_url: str) -> list[tuple[str, str]]:
    """Return up to MAX_CONTACT_LINKS (url, page_kind) tuples, deduped."""
    soup = BeautifulSoup(html, "lxml")
    seen: dict[str, str] = {}
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if not href or href.startswith("#") or href.startswith("mailto:") or href.startswith("javascript:"):
            continue
        full = urljoin(base_url, href)
        if not _same_host(full, base_url):
            continue
        kind = classify_page_kind(href, a.get_text(strip=True))
        if kind is None:
            continue
        # strip fragment
        full = full.split("#", 1)[0].rstrip("/") or full
        if full in seen:
            continue
        seen[full] = kind
        if len(seen) >= MAX_CONTACT_LINKS:
            break
    return list(seen.items())
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
python -m pytest tests/test_links.py -v
```

Expected: 5 passed.

- [ ] **Step 6: Commit**

```bash
git add pipeline/links.py tests/test_links.py tests/fixtures/sample_homepage.html
git commit -m "Add contact-like link finder and page-kind classifier"
```

---

## Task 8: URL discovery (SerpAPI + heuristic)

**Files:**
- Create: `pipeline/discover.py`
- Create: `tests/test_discover.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_discover.py`:
```python
"""Tests for pipeline.discover."""
from pipeline.discover import is_plausible_clt_domain, pick_best_url


def test_is_plausible_rejects_social_platforms():
    name = "Proud Ground"
    assert not is_plausible_clt_domain("https://facebook.com/proudground", name)
    assert not is_plausible_clt_domain("https://www.linkedin.com/company/proudground", name)
    assert not is_plausible_clt_domain("https://twitter.com/proudground", name)
    assert not is_plausible_clt_domain("https://x.com/proudground", name)
    assert not is_plausible_clt_domain("https://instagram.com/proudground", name)
    assert not is_plausible_clt_domain("https://www.youtube.com/c/proudground", name)


def test_is_plausible_rejects_news_and_directory_sites():
    assert not is_plausible_clt_domain("https://nytimes.com/article", "Proud Ground")
    assert not is_plausible_clt_domain("https://opb.org/news", "Proud Ground")
    assert not is_plausible_clt_domain("https://yelp.com/biz/proudground", "Proud Ground")


def test_is_plausible_requires_name_token_in_domain():
    # short tokens and stop-words don't count
    assert not is_plausible_clt_domain("https://landtrust.org/", "The Land Trust")
    assert is_plausible_clt_domain("https://proudground.org/", "Proud Ground")
    assert is_plausible_clt_domain("https://www.sabincdc.org/", "Sabin CDC")


def test_pick_best_url_returns_first_plausible():
    organic = [
        {"link": "https://facebook.com/proudground"},
        {"link": "https://proudground.org/"},
        {"link": "https://example.com/"},
    ]
    assert pick_best_url(organic, name="Proud Ground") == "https://proudground.org/"


def test_pick_best_url_returns_none_when_no_match():
    organic = [{"link": "https://facebook.com/x"}, {"link": "https://yelp.com/x"}]
    assert pick_best_url(organic, name="Whatever CLT") is None


def test_pick_best_url_handles_missing_link_field():
    organic = [{}, {"link": "https://proudground.org/"}]
    assert pick_best_url(organic, name="Proud Ground") == "https://proudground.org/"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
python -m pytest tests/test_discover.py -v
```

Expected: ImportError.

- [ ] **Step 3: Implement `pipeline/discover.py`**

```python
"""Discover a CLT's website using SerpAPI + a domain plausibility heuristic."""
from __future__ import annotations

import re
from urllib.parse import urlparse

# Hosts we never want to pick as a CLT's "website".
BLOCKED_HOSTS = {
    "facebook.com", "m.facebook.com",
    "linkedin.com", "www.linkedin.com",
    "twitter.com", "x.com",
    "instagram.com", "www.instagram.com",
    "youtube.com", "www.youtube.com", "m.youtube.com",
    "yelp.com", "www.yelp.com",
    "nytimes.com", "www.nytimes.com",
    "opb.org", "www.opb.org",
    "wikipedia.org", "en.wikipedia.org",
    "guidestar.org", "www.guidestar.org",
    "candid.org", "www.candid.org",
    "charitynavigator.org", "www.charitynavigator.org",
    "propublica.org", "www.propublica.org",
}

STOP_TOKENS = {
    "the", "of", "and", "for", "a", "an", "land", "trust", "community",
    "clt", "cdc", "inc", "incorporated", "association", "fund", "co",
}

_TOKEN = re.compile(r"[a-z0-9]+")


def _name_tokens(name: str) -> set[str]:
    return {t for t in _TOKEN.findall(name.lower()) if len(t) > 3 and t not in STOP_TOKENS}


def is_plausible_clt_domain(url: str, name: str) -> bool:
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    if not host or host in BLOCKED_HOSTS:
        return False
    bare = host[4:] if host.startswith("www.") else host
    if any(bare.endswith(b[4:] if b.startswith("www.") else b) for b in BLOCKED_HOSTS):
        return False
    tokens = _name_tokens(name)
    if not tokens:
        # Name has no distinctive tokens; can't be confident — reject.
        return False
    return any(t in bare.replace("-", "").replace(".", "") for t in tokens)


def pick_best_url(organic_results: list[dict], name: str) -> str | None:
    for r in organic_results:
        link = r.get("link")
        if not link:
            continue
        if is_plausible_clt_domain(link, name):
            return link
    return None
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
python -m pytest tests/test_discover.py -v
```

Expected: 6 passed.

- [ ] **Step 5: Add the orchestration function**

Append to `pipeline/discover.py`:
```python
from pipeline.serpapi import SerpApiClient


def discover_url(client: SerpApiClient, *, name: str, city: str | None, state: str | None) -> str | None:
    """Run the canonical discovery query and return a plausible CLT URL or None."""
    parts = [f'"{name}"']
    if city:
        parts.append(f'"{city}"')
    if state:
        parts.append(state)
    parts.append("community land trust")
    query = " ".join(parts)
    data = client.search(query)
    return pick_best_url(data.get("organic_results", []), name)
```

- [ ] **Step 6: Commit**

```bash
git add pipeline/discover.py tests/test_discover.py
git commit -m "Add URL discovery via SerpAPI + domain plausibility heuristic"
```

---

## Task 9: Email extractor

**Files:**
- Create: `pipeline/extractor.py`
- Create: `tests/test_extractor.py`
- Create: `tests/fixtures/sample_contact.html`

- [ ] **Step 1: Create the HTML fixture**

Create `tests/fixtures/sample_contact.html`:
```html
<!doctype html>
<html><body>
  <h1>Contact us</h1>
  <p>Email <a href="mailto:info@sampleclt.org">info@sampleclt.org</a> for info.</p>
  <p>Director: director@sampleclt.org</p>
  <p>Programs: programs [at] sampleclt [dot] org</p>
  <p>Outreach: outreach (at) sampleclt (dot) org</p>
  <p>Volunteer: volunteer AT sampleclt DOT org</p>
  <p>Image: <img src="logo@2x.png" alt="logo"></p>
  <p>Junk: noreply@example.com (test address)</p>
  <p>Wix: form@wixpress.com</p>
  <p>Sentry: noreply@sentry.io</p>
</body></html>
```

- [ ] **Step 2: Write the failing tests**

Create `tests/test_extractor.py`:
```python
"""Tests for pipeline.extractor."""
from pathlib import Path

from pipeline.extractor import extract_emails, normalize_email

FIXTURE = Path(__file__).parent / "fixtures" / "sample_contact.html"


def test_normalize_email_lowercases_and_strips():
    assert normalize_email("  Info@SampleCLT.org. ") == "info@sampleclt.org"


def test_extract_emails_picks_up_mailto():
    html = FIXTURE.read_text()
    found = extract_emails(html)
    sources = {(e["email"], e["source"]) for e in found}
    assert ("info@sampleclt.org", "mailto") in sources


def test_extract_emails_picks_up_visible_text():
    html = FIXTURE.read_text()
    found = extract_emails(html)
    assert any(e["email"] == "director@sampleclt.org" and e["source"] == "text" for e in found)


def test_extract_emails_deobfuscates_at_and_dot_patterns():
    html = FIXTURE.read_text()
    emails = {e["email"] for e in extract_emails(html) if e["source"] == "deobfuscated"}
    assert "programs@sampleclt.org" in emails
    assert "outreach@sampleclt.org" in emails
    assert "volunteer@sampleclt.org" in emails


def test_extract_emails_filters_junk_domains():
    html = FIXTURE.read_text()
    emails = {e["email"] for e in extract_emails(html)}
    assert "noreply@example.com" not in emails
    assert "form@wixpress.com" not in emails
    assert "noreply@sentry.io" not in emails


def test_extract_emails_filters_image_filename_false_positive():
    # logo@2x.png in <img src> should NOT register as an email.
    html = FIXTURE.read_text()
    emails = {e["email"] for e in extract_emails(html)}
    assert not any(e.endswith(".png") for e in emails)


def test_extract_emails_includes_context_snippet():
    html = FIXTURE.read_text()
    found = extract_emails(html)
    director = next(e for e in found if e["email"] == "director@sampleclt.org")
    assert "Director" in director["context"]
    assert len(director["context"]) <= 200
```

- [ ] **Step 3: Run tests to verify they fail**

```bash
python -m pytest tests/test_extractor.py -v
```

Expected: ImportError.

- [ ] **Step 4: Implement `pipeline/extractor.py`**

```python
"""Email extraction from stored HTML.

Three sources, in order of confidence: mailto: links, visible-text regex,
deobfuscated patterns. All results are normalized and filtered against a
domain blocklist before return.
"""
from __future__ import annotations

import re
from typing import Iterable

from bs4 import BeautifulSoup

EMAIL_RE = re.compile(
    r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b"
)

# Patterns like: name [at] domain [dot] org, with [], (), or just words.
DEOBFUSCATE_RE = re.compile(
    r"\b([A-Za-z0-9._%+\-]+)\s*[\[\(]?\s*(?:at|@)\s*[\]\)]?\s*"
    r"([A-Za-z0-9.\-]+?)\s*[\[\(]?\s*(?:dot|\.)\s*[\]\)]?\s*"
    r"([A-Za-z]{2,})\b",
    re.IGNORECASE,
)

# Domains we never trust as a real CLT contact email.
BLOCKED_EMAIL_DOMAINS = {
    "example.com", "example.org", "example.net",
    "sentry.io",
    "wixpress.com",
    "squarespace.com",
    "wordpress.com",
    "godaddy.com",
    "domain.com",
    "yourdomain.com",
    "test.com",
}

CONTEXT_RADIUS = 100  # chars on each side of the match


def normalize_email(raw: str) -> str:
    return raw.strip().rstrip(".,;:").lower()


def _domain(email: str) -> str:
    return email.rsplit("@", 1)[-1]


def _is_blocked(email: str) -> bool:
    d = _domain(email)
    return d in BLOCKED_EMAIL_DOMAINS or d.startswith("wixpress.")


def _snippet(text: str, start: int, end: int) -> str:
    lo = max(0, start - CONTEXT_RADIUS)
    hi = min(len(text), end + CONTEXT_RADIUS)
    return text[lo:hi].replace("\n", " ").strip()


def extract_emails(html: str) -> list[dict]:
    """Return a list of {email, source, context} dicts. Deduped by (email, source)."""
    soup = BeautifulSoup(html, "lxml")
    found: dict[tuple[str, str], dict] = {}

    # 1) mailto: links
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if href.lower().startswith("mailto:"):
            raw = href.split(":", 1)[1].split("?", 1)[0]
            email = normalize_email(raw)
            if EMAIL_RE.fullmatch(email) and not _is_blocked(email):
                key = (email, "mailto")
                found.setdefault(key, {
                    "email": email, "source": "mailto",
                    "context": a.get_text(strip=True) or email,
                })

    # 2) visible text — strip script/style/img-attribute noise
    for tag in soup(["script", "style"]):
        tag.decompose()
    text = soup.get_text(" ", strip=False)

    for m in EMAIL_RE.finditer(text):
        email = normalize_email(m.group(0))
        if _is_blocked(email):
            continue
        key = (email, "text")
        if key in found:
            continue
        found.setdefault(key, {
            "email": email, "source": "text",
            "context": _snippet(text, m.start(), m.end()),
        })

    # 3) deobfuscated
    for m in DEOBFUSCATE_RE.finditer(text):
        local, host, tld = m.group(1), m.group(2), m.group(3)
        candidate = normalize_email(f"{local}@{host}.{tld}")
        if not EMAIL_RE.fullmatch(candidate) or _is_blocked(candidate):
            continue
        key = (candidate, "deobfuscated")
        if key in found or (candidate, "text") in found or (candidate, "mailto") in found:
            continue
        found[key] = {
            "email": candidate, "source": "deobfuscated",
            "context": _snippet(text, m.start(), m.end()),
        }

    return list(found.values())
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
python -m pytest tests/test_extractor.py -v
```

Expected: 7 passed.

- [ ] **Step 6: Commit**

```bash
git add pipeline/extractor.py tests/test_extractor.py tests/fixtures/sample_contact.html
git commit -m "Add email extractor: mailto, visible text, deobfuscated, blocklist"
```

---

## Task 10: Crawler

**Files:**
- Create: `pipeline/crawler.py`
- Create: `tests/test_crawler.py`

The crawler combines the throttled session, robots checker, link finder, and DB persistence. We test it with mocked HTTP and a fake DB layer.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_crawler.py`:
```python
"""Tests for pipeline.crawler.crawl_one."""
from pathlib import Path
from unittest import mock

import responses

from pipeline.crawler import crawl_one, CrawlResult
from pipeline.http import ThrottledSession
from pipeline.robots import RobotsCache


HOMEPAGE = """
<html><body>
  <a href="/about">About</a>
  <a href="/contact">Contact</a>
  <a href="/staff">Staff</a>
</body></html>
"""


@responses.activate
def test_crawl_one_fetches_homepage_plus_contact_links(tmp_path):
    base = "https://sampleclt.org"
    responses.add(responses.GET, f"{base}/robots.txt", body="", status=200)
    responses.add(responses.GET, f"{base}/", body=HOMEPAGE, status=200)
    responses.add(responses.GET, f"{base}/about", body="<p>about</p>", status=200)
    responses.add(responses.GET, f"{base}/contact", body="<p>contact</p>", status=200)
    responses.add(responses.GET, f"{base}/staff", body="<p>staff</p>", status=200)

    session = ThrottledSession(per_domain_delay=0, sleep=lambda s: None)
    robots = RobotsCache()
    result = crawl_one(
        clt_id="sample-clt",
        url=f"{base}/",
        session=session,
        robots=robots,
        html_dir=tmp_path,
    )
    assert isinstance(result, CrawlResult)
    assert result.success
    kinds = sorted(p.page_kind for p in result.pages)
    assert kinds == ["about", "contact", "home", "staff"]
    assert all(Path(p.html_path).exists() for p in result.pages)
    # files written under html_dir/<clt_id>/
    assert all(Path(p.html_path).is_relative_to(tmp_path / "sample-clt") for p in result.pages)


@responses.activate
def test_crawl_one_records_404_as_page_with_error(tmp_path):
    base = "https://sampleclt.org"
    responses.add(responses.GET, f"{base}/robots.txt", body="", status=200)
    responses.add(responses.GET, f"{base}/", body="<a href='/contact'>c</a>", status=200)
    responses.add(responses.GET, f"{base}/contact", status=404)

    session = ThrottledSession(per_domain_delay=0, sleep=lambda s: None)
    robots = RobotsCache()
    result = crawl_one("c", f"{base}/", session, robots, tmp_path)
    contact = next(p for p in result.pages if p.page_kind == "contact")
    assert contact.http_status == 404
    assert contact.error is not None


@responses.activate
def test_crawl_one_homepage_failure_marks_overall_failure(tmp_path):
    base = "https://deadclt.org"
    responses.add(responses.GET, f"{base}/robots.txt", body="", status=200)
    responses.add(responses.GET, f"{base}/", status=500)
    responses.add(responses.GET, f"{base}/", status=500)  # retry

    session = ThrottledSession(per_domain_delay=0, sleep=lambda s: None, retry_backoff=0)
    robots = RobotsCache()
    result = crawl_one("c", f"{base}/", session, robots, tmp_path)
    assert not result.success
    assert result.pages[0].page_kind == "home"
    assert result.pages[0].http_status == 500


@responses.activate
def test_crawl_one_respects_robots_disallow(tmp_path):
    base = "https://sampleclt.org"
    responses.add(responses.GET, f"{base}/robots.txt",
                  body="User-agent: *\nDisallow: /private/", status=200)
    responses.add(responses.GET, f"{base}/", body="<a href='/private/contact'>c</a>", status=200)

    session = ThrottledSession(per_domain_delay=0, sleep=lambda s: None)
    robots = RobotsCache()
    result = crawl_one("c", f"{base}/", session, robots, tmp_path)
    private = next((p for p in result.pages if p.url.endswith("/private/contact")), None)
    assert private is not None
    assert private.error == "robots-disallowed"
    assert private.html_path is None
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
python -m pytest tests/test_crawler.py -v
```

Expected: ImportError.

- [ ] **Step 3: Implement `pipeline/crawler.py`**

```python
"""Crawl a CLT's homepage + contact-like pages, store HTML on disk."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path

import requests

from pipeline.http import ThrottledSession
from pipeline.links import find_contact_links
from pipeline.robots import RobotsCache


@dataclass
class FetchedPage:
    url: str
    page_kind: str  # 'home' | 'about' | 'contact' | 'staff' | 'team' | 'board'
    http_status: int | None
    html_path: str | None  # absolute path on disk, or None on error
    content_hash: str | None
    error: str | None


@dataclass
class CrawlResult:
    clt_id: str
    pages: list[FetchedPage] = field(default_factory=list)

    @property
    def success(self) -> bool:
        # Success requires at least one page persisted to disk.
        return any(p.html_path is not None for p in self.pages)


def _content_path(html_dir: Path, clt_id: str, page_kind: str, body: bytes) -> Path:
    h = hashlib.sha256(body).hexdigest()[:8]
    out = html_dir / clt_id
    out.mkdir(parents=True, exist_ok=True)
    return out / f"{page_kind}-{h}.html"


def _fetch(session: ThrottledSession, robots: RobotsCache, url: str, page_kind: str,
           html_dir: Path, clt_id: str) -> FetchedPage:
    if not robots.allowed(url):
        return FetchedPage(url=url, page_kind=page_kind, http_status=None,
                           html_path=None, content_hash=None, error="robots-disallowed")
    try:
        resp = session.get(url)
    except requests.RequestException as exc:
        return FetchedPage(url=url, page_kind=page_kind, http_status=None,
                           html_path=None, content_hash=None, error=str(exc))
    if resp.status_code != 200:
        return FetchedPage(url=url, page_kind=page_kind, http_status=resp.status_code,
                           html_path=None, content_hash=None,
                           error=f"http-{resp.status_code}")
    body = resp.content
    path = _content_path(html_dir, clt_id, page_kind, body)
    path.write_bytes(body)
    return FetchedPage(url=url, page_kind=page_kind, http_status=200,
                       html_path=str(path), content_hash=hashlib.sha256(body).hexdigest(),
                       error=None)


def crawl_one(clt_id: str, url: str, session: ThrottledSession,
              robots: RobotsCache, html_dir: Path) -> CrawlResult:
    """Crawl one CLT: homepage + contact-like links. Returns CrawlResult with all pages."""
    result = CrawlResult(clt_id=clt_id)
    home = _fetch(session, robots, url, "home", Path(html_dir), clt_id)
    result.pages.append(home)
    if home.html_path is None:
        return result
    html = Path(home.html_path).read_text(encoding="utf-8", errors="replace")
    for link_url, kind in find_contact_links(html, base_url=url):
        page = _fetch(session, robots, link_url, kind, Path(html_dir), clt_id)
        result.pages.append(page)
    return result
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
python -m pytest tests/test_crawler.py -v
```

Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add pipeline/crawler.py tests/test_crawler.py
git commit -m "Add crawler for homepage + contact-like pages with on-disk HTML"
```

---

## Task 11: Seeds — existing JSON + state SerpAPI sweep

The two third-party directories (Grounded Solutions, Center for CLT Innovation) require live HTML inspection to write parsers. Defer those to Task 14 once the rest of the pipeline is working. For now, seed from the existing JSON and prepare the state-by-state SerpAPI sweep.

**Files:**
- Create: `pipeline/seeds.py`
- Create: `tests/test_seeds.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_seeds.py`:
```python
"""Tests for pipeline.seeds — slug, parse-existing, state-sweep helpers."""
import json
from pathlib import Path

from pipeline.seeds import slugify, parse_existing_clts, build_state_sweep_query, parse_state_sweep_results


def test_slugify_basic():
    assert slugify("Proud Ground") == "proud-ground"
    assert slugify("  Sabin CDC  ") == "sabin-cdc"
    assert slugify("DevNW (Springfield)") == "devnw-springfield"
    assert slugify("Café Land Trust") == "cafe-land-trust"


def test_parse_existing_clts(tmp_path):
    sample = [
        {"id": "x", "name": "X CLT", "location": "Portland, OR", "state": "OR",
         "url": "https://x.org", "notes": "n"},
        {"id": "y", "name": "Y CLT", "location": "Bend, OR", "state": "OR",
         "url": None, "notes": ""},
    ]
    p = tmp_path / "clts.json"
    p.write_text(json.dumps(sample))
    rows = parse_existing_clts(p)
    assert rows[0] == {
        "id": "x", "name": "X CLT", "city": "Portland", "state": "OR",
        "url": "https://x.org", "source": "existing", "status": "url_found", "notes": "n",
    }
    assert rows[1]["status"] == "discovered"
    assert rows[1]["url"] is None


def test_build_state_sweep_query():
    assert build_state_sweep_query("OR") == '"community land trust" "Oregon"'
    assert build_state_sweep_query("CA") == '"community land trust" "California"'


def test_parse_state_sweep_results_extracts_org_candidates():
    payload = {"organic_results": [
        {"title": "Proud Ground - Portland, OR", "link": "https://proudground.org/"},
        {"title": "What is a CLT? - News article", "link": "https://nytimes.com/foo"},
        {"title": "Olympia Community Land Trust", "link": "https://olympiaclt.org/about"},
    ]}
    rows = parse_state_sweep_results(payload, state="OR")
    names = {r["name"] for r in rows}
    assert "Proud Ground" in names
    assert "Olympia Community Land Trust" in names
    assert all(r["state"] == "OR" for r in rows)
    assert all(r["source"] == "serpapi-sweep" for r in rows)
    assert all(r["status"] == "url_found" for r in rows)
    # news result filtered out
    assert not any("nytimes" in (r.get("url") or "") for r in rows)
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
python -m pytest tests/test_seeds.py -v
```

Expected: ImportError.

- [ ] **Step 3: Implement `pipeline/seeds.py`**

```python
"""Seed candidate CLTs from existing JSON and SerpAPI state sweeps."""
from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

from pipeline.discover import is_plausible_clt_domain

US_STATES = {
    "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas",
    "CA": "California", "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware",
    "FL": "Florida", "GA": "Georgia", "HI": "Hawaii", "ID": "Idaho",
    "IL": "Illinois", "IN": "Indiana", "IA": "Iowa", "KS": "Kansas",
    "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine", "MD": "Maryland",
    "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota", "MS": "Mississippi",
    "MO": "Missouri", "MT": "Montana", "NE": "Nebraska", "NV": "Nevada",
    "NH": "New Hampshire", "NJ": "New Jersey", "NM": "New Mexico", "NY": "New York",
    "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio", "OK": "Oklahoma",
    "OR": "Oregon", "PA": "Pennsylvania", "RI": "Rhode Island", "SC": "South Carolina",
    "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas", "UT": "Utah",
    "VT": "Vermont", "VA": "Virginia", "WA": "Washington", "WV": "West Virginia",
    "WI": "Wisconsin", "WY": "Wyoming", "DC": "District of Columbia",
}


def slugify(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    s = re.sub(r"[()\[\]{}]", "", s).strip().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s


def parse_existing_clts(json_path: Path) -> list[dict]:
    """Read src/data/clts.json into inv_clts-shaped rows (source='existing')."""
    data = json.loads(Path(json_path).read_text(encoding="utf-8"))
    rows: list[dict] = []
    for entry in data:
        loc = entry.get("location", "") or ""
        city = loc.split(",", 1)[0].strip() if "," in loc else None
        rows.append({
            "id": entry["id"],
            "name": entry["name"],
            "city": city,
            "state": entry.get("state"),
            "url": entry.get("url") or None,
            "source": "existing",
            "status": "url_found" if entry.get("url") else "discovered",
            "notes": entry.get("notes") or None,
        })
    return rows


def build_state_sweep_query(state_code: str) -> str:
    return f'"community land trust" "{US_STATES[state_code]}"'


_TITLE_TRIM = re.compile(r"\s*[-|–·•].*$")


def _name_from_title(title: str) -> str | None:
    """Strip site-name suffixes from SERP titles. Heuristic, not exact."""
    if not title:
        return None
    name = _TITLE_TRIM.sub("", title).strip()
    return name or None


def parse_state_sweep_results(serp_payload: dict, state: str) -> list[dict]:
    """Convert a state sweep SERP into inv_clts-shaped candidate rows.

    Only keeps results whose domain looks like a real CLT site (per
    discover.is_plausible_clt_domain).
    """
    rows: list[dict] = []
    seen_ids: set[str] = set()
    for r in serp_payload.get("organic_results", []):
        link = r.get("link")
        title = r.get("title", "")
        name = _name_from_title(title)
        if not name or not link:
            continue
        if not is_plausible_clt_domain(link, name):
            continue
        cid = slugify(name)
        if cid in seen_ids:
            continue
        seen_ids.add(cid)
        rows.append({
            "id": cid,
            "name": name,
            "city": None,
            "state": state,
            "url": link,
            "source": "serpapi-sweep",
            "status": "url_found",
            "notes": None,
        })
    return rows
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
python -m pytest tests/test_seeds.py -v
```

Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add pipeline/seeds.py tests/test_seeds.py
git commit -m "Add seeds: slug, existing-JSON parser, state-sweep query and parser"
```

---

## Task 12: Export to clts.json

**Files:**
- Create: `pipeline/export.py`
- Create: `tests/test_export.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_export.py`:
```python
"""Tests for pipeline.export.merge_with_existing — pure merge logic."""
from pipeline.export import merge_with_existing, default_new_entry


def test_existing_entry_preserved_verbatim():
    existing = [{
        "id": "proud-ground", "name": "Proud Ground", "location": "Portland, OR",
        "state": "OR", "founded": 1999, "focus": ["housing"],
        "axes": {"housing": 94, "agriculture": 3, "commercial": 3},
        "url": "https://www.proudground.org",
        "scale": "740+ households", "notes": "Oregon's largest CLT",
    }]
    inv = [{
        "id": "proud-ground", "name": "Proud Ground", "city": "Portland",
        "state": "OR", "url": "https://www.proudground.org",
        "notes": "should be ignored — existing wins",
    }]
    merged = merge_with_existing(inv, existing)
    out = next(e for e in merged if e["id"] == "proud-ground")
    assert out["founded"] == 1999
    assert out["axes"] == {"housing": 94, "agriculture": 3, "commercial": 3}
    assert out["notes"] == "Oregon's largest CLT"
    assert out["url"] == "https://www.proudground.org"


def test_new_entry_uses_defaults():
    inv = [{
        "id": "foo-clt", "name": "Foo CLT", "city": "Seattle", "state": "WA",
        "url": "https://fooclt.org", "notes": "from sweep",
    }]
    merged = merge_with_existing(inv, [])
    out = merged[0]
    assert out["id"] == "foo-clt"
    assert out["location"] == "Seattle, WA"
    assert out["founded"] is None
    assert out["focus"] == ["housing"]
    assert out["axes"] == {"housing": 90, "agriculture": 5, "commercial": 5}
    assert out["scale"] is None
    assert out["notes"] == "from sweep"


def test_skips_inv_entries_without_url():
    inv = [{"id": "a", "name": "A", "city": "X", "state": "OR", "url": None}]
    assert merge_with_existing(inv, []) == []


def test_sorted_by_state_then_name():
    inv = [
        {"id": "z", "name": "Z", "city": "X", "state": "WA", "url": "https://z.org"},
        {"id": "a", "name": "A", "city": "X", "state": "OR", "url": "https://a.org"},
        {"id": "b", "name": "B", "city": "X", "state": "OR", "url": "https://b.org"},
    ]
    merged = merge_with_existing(inv, [])
    assert [e["id"] for e in merged] == ["a", "b", "z"]


def test_emails_never_appear_in_output():
    inv = [{"id": "a", "name": "A", "city": "X", "state": "OR", "url": "https://a.org",
            "email": "private@a.org"}]  # even if passed in, never emit
    merged = merge_with_existing(inv, [])
    assert "email" not in merged[0]
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
python -m pytest tests/test_export.py -v
```

Expected: ImportError.

- [ ] **Step 3: Implement `pipeline/export.py`**

```python
"""Rebuild src/data/clts.json from inv_clts. Emails are never written here."""
from __future__ import annotations

import json
from pathlib import Path

from pipeline.config import SITE_CLTS_JSON
from pipeline.db import connect


def default_new_entry(inv_row: dict) -> dict:
    """Schema-shaped entry for a new CLT (one not already in clts.json)."""
    location = ", ".join(p for p in (inv_row.get("city"), inv_row.get("state")) if p)
    return {
        "id": inv_row["id"],
        "name": inv_row["name"],
        "location": location or None,
        "state": inv_row.get("state"),
        "founded": None,
        "focus": ["housing"],
        "axes": {"housing": 90, "agriculture": 5, "commercial": 5},
        "url": inv_row["url"],
        "scale": None,
        "notes": inv_row.get("notes"),
    }


def merge_with_existing(inv_rows: list[dict], existing: list[dict]) -> list[dict]:
    by_id = {e["id"]: e for e in existing}
    out: list[dict] = []
    for row in inv_rows:
        if not row.get("url"):
            continue
        if row["id"] in by_id:
            # Preserve hand-curated entry exactly as-is.
            out.append(by_id[row["id"]])
        else:
            out.append(default_new_entry(row))
    out.sort(key=lambda e: ((e.get("state") or "").lower(), e["name"].lower()))
    return out


def export_to_clts_json(*, dry_run: bool = False) -> dict:
    """Pull inv_clts → merge with existing clts.json → write. Returns summary dict."""
    with connect() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT id, name, city, state, url, notes "
            "FROM inv_clts WHERE url IS NOT NULL"
        )
        inv_rows = [
            {"id": r[0], "name": r[1], "city": r[2], "state": r[3], "url": r[4], "notes": r[5]}
            for r in cur.fetchall()
        ]
    existing = json.loads(Path(SITE_CLTS_JSON).read_text(encoding="utf-8"))
    merged = merge_with_existing(inv_rows, existing)

    summary = {
        "existing_preserved": sum(1 for e in merged if any(x["id"] == e["id"] for x in existing)),
        "new": sum(1 for e in merged if not any(x["id"] == e["id"] for x in existing)),
        "total": len(merged),
        "skipped_no_url": sum(1 for r in inv_rows if not r["url"]),
    }
    if not dry_run:
        Path(SITE_CLTS_JSON).write_text(
            json.dumps(merged, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    return summary
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
python -m pytest tests/test_export.py -v
```

Expected: 5 passed.

- [ ] **Step 5: Commit**

```bash
git add pipeline/export.py tests/test_export.py
git commit -m "Add exporter that rebuilds clts.json preserving hand-curated fields"
```

---

## Task 13: Stage runners (DB-aware orchestration helpers)

These wrap the pure pieces above with DB read/write logic so the notebook orchestrator stays trivial. We unit-test the bits that don't touch DB; DB integration is exercised by the notebook smoke run.

**Files:**
- Create: `pipeline/stages.py`
- Create: `tests/test_stages.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_stages.py`:
```python
"""Tests for pipeline.stages — only the pure helpers, not DB-touching runners."""
from pipeline.stages import upsert_sql, page_insert_sql, email_insert_sql


def test_upsert_sql_uses_on_conflict_do_update():
    sql = upsert_sql()
    assert "INSERT INTO inv_clts" in sql
    assert "ON CONFLICT (id)" in sql
    assert "DO UPDATE" in sql
    assert "updated_at = now()" in sql


def test_page_insert_sql_returns_id():
    assert "RETURNING id" in page_insert_sql()


def test_email_insert_sql_has_required_columns():
    sql = email_insert_sql()
    for col in ("clt_id", "page_id", "email", "source", "context"):
        assert col in sql
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
python -m pytest tests/test_stages.py -v
```

Expected: ImportError.

- [ ] **Step 3: Implement `pipeline/stages.py`**

```python
"""DB-aware stage runners. Each function picks up its work from inv_clts.status."""
from __future__ import annotations

from pathlib import Path

from pipeline.config import HTML_DIR, load_env
from pipeline.crawler import crawl_one
from pipeline.db import connect
from pipeline.discover import discover_url
from pipeline.extractor import extract_emails
from pipeline.http import ThrottledSession
from pipeline.robots import RobotsCache
from pipeline.serpapi import PostgresCache, SerpApiClient


def upsert_sql() -> str:
    return """
INSERT INTO inv_clts (id, name, city, state, url, source, status, notes)
VALUES (%(id)s, %(name)s, %(city)s, %(state)s, %(url)s, %(source)s, %(status)s, %(notes)s)
ON CONFLICT (id) DO UPDATE SET
  name = COALESCE(EXCLUDED.name, inv_clts.name),
  city = COALESCE(EXCLUDED.city, inv_clts.city),
  state = COALESCE(EXCLUDED.state, inv_clts.state),
  url = COALESCE(inv_clts.url, EXCLUDED.url),
  notes = COALESCE(inv_clts.notes, EXCLUDED.notes),
  updated_at = now()
"""


def page_insert_sql() -> str:
    return """
INSERT INTO inv_pages (clt_id, url, page_kind, http_status, html_path, content_hash, error)
VALUES (%(clt_id)s, %(url)s, %(page_kind)s, %(http_status)s, %(html_path)s, %(content_hash)s, %(error)s)
ON CONFLICT (clt_id, url) DO UPDATE SET
  http_status = EXCLUDED.http_status,
  html_path = EXCLUDED.html_path,
  content_hash = EXCLUDED.content_hash,
  error = EXCLUDED.error,
  fetched_at = now()
RETURNING id
"""


def email_insert_sql() -> str:
    return """
INSERT INTO inv_emails (clt_id, page_id, email, source, context)
VALUES (%(clt_id)s, %(page_id)s, %(email)s, %(source)s, %(context)s)
"""


def upsert_clts(rows: list[dict]) -> None:
    if not rows:
        return
    with connect() as conn, conn.cursor() as cur:
        for r in rows:
            cur.execute(upsert_sql(), r)
        conn.commit()


def run_discover() -> dict:
    """For each inv_clts.status='discovered' (no url), find a URL via SerpAPI."""
    env = load_env()
    client = SerpApiClient(api_key=env["SERPAPI_KEY"], cache=PostgresCache())
    n_found = n_missed = 0
    with connect() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT id, name, city, state FROM inv_clts "
            "WHERE status = 'discovered' AND url IS NULL"
        )
        rows = cur.fetchall()

    for clt_id, name, city, state in rows:
        url = discover_url(client, name=name, city=city, state=state)
        new_status = "url_found" if url else "url_not_found"
        if url:
            n_found += 1
        else:
            n_missed += 1
        with connect() as conn, conn.cursor() as cur:
            cur.execute(
                "UPDATE inv_clts SET url = COALESCE(%s, url), status = %s, "
                "updated_at = now() WHERE id = %s",
                (url, new_status, clt_id),
            )
            conn.commit()
    return {"checked": len(rows), "found": n_found, "missed": n_missed}


def run_crawl() -> dict:
    """For each inv_clts.status='url_found', fetch homepage + contact pages."""
    HTML_DIR.mkdir(parents=True, exist_ok=True)
    session = ThrottledSession()
    robots = RobotsCache()
    n_ok = n_fail = 0
    with connect() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT id, url FROM inv_clts WHERE status = 'url_found' AND url IS NOT NULL"
        )
        rows = cur.fetchall()

    for clt_id, url in rows:
        result = crawl_one(clt_id, url, session, robots, HTML_DIR)
        with connect() as conn, conn.cursor() as cur:
            for page in result.pages:
                cur.execute(page_insert_sql(), {
                    "clt_id": clt_id,
                    "url": page.url,
                    "page_kind": page.page_kind,
                    "http_status": page.http_status,
                    "html_path": page.html_path,
                    "content_hash": page.content_hash,
                    "error": page.error,
                })
            new_status = "crawled" if result.success else "crawl_failed"
            cur.execute("UPDATE inv_clts SET status = %s, updated_at = now() WHERE id = %s",
                        (new_status, clt_id))
            conn.commit()
        if result.success:
            n_ok += 1
        else:
            n_fail += 1
    return {"crawled": len(rows), "ok": n_ok, "failed": n_fail}


def run_rescue() -> dict:
    """For each inv_clts.status='crawl_failed', re-query SerpAPI for a fresh URL."""
    env = load_env()
    client = SerpApiClient(api_key=env["SERPAPI_KEY"], cache=PostgresCache())
    rescued = 0
    with connect() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT id, name, city, state, url FROM inv_clts WHERE status = 'crawl_failed'"
        )
        rows = cur.fetchall()

    for clt_id, name, city, state, old_url in rows:
        # Broader query: drop the "community land trust" suffix.
        q_parts = [f'"{name}"']
        if city:
            q_parts.append(city)
        if state:
            q_parts.append(state)
        data = client.search(" ".join(q_parts))
        from pipeline.discover import pick_best_url
        new_url = pick_best_url(data.get("organic_results", []), name)
        if new_url and new_url != old_url:
            with connect() as conn, conn.cursor() as cur:
                cur.execute(
                    "UPDATE inv_clts SET url = %s, status = 'url_found', updated_at = now() "
                    "WHERE id = %s",
                    (new_url, clt_id),
                )
                conn.commit()
            rescued += 1
    return {"checked": len(rows), "rescued": rescued}


def run_extract() -> dict:
    """For each inv_clts.status='crawled', extract emails from stored HTML."""
    n_clts = n_emails = 0
    with connect() as conn, conn.cursor() as cur:
        cur.execute("SELECT id FROM inv_clts WHERE status = 'crawled'")
        clt_ids = [r[0] for r in cur.fetchall()]

    for clt_id in clt_ids:
        clt_emails = 0
        with connect() as conn, conn.cursor() as cur:
            cur.execute(
                "SELECT id, html_path FROM inv_pages "
                "WHERE clt_id = %s AND html_path IS NOT NULL",
                (clt_id,),
            )
            pages = cur.fetchall()

        for page_id, html_path in pages:
            html = Path(html_path).read_text(encoding="utf-8", errors="replace")
            for e in extract_emails(html):
                with connect() as conn, conn.cursor() as cur:
                    cur.execute(email_insert_sql(), {
                        "clt_id": clt_id,
                        "page_id": page_id,
                        "email": e["email"],
                        "source": e["source"],
                        "context": e["context"],
                    })
                    conn.commit()
                clt_emails += 1

        with connect() as conn, conn.cursor() as cur:
            cur.execute(
                "UPDATE inv_clts SET status = 'extracted', updated_at = now() WHERE id = %s",
                (clt_id,),
            )
            conn.commit()
        n_clts += 1
        n_emails += clt_emails
    return {"clts": n_clts, "emails_inserted": n_emails}
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
python -m pytest tests/test_stages.py -v
```

Expected: 3 passed.

- [ ] **Step 5: Run full unit test suite to confirm nothing regressed**

```bash
python -m pytest -v
```

Expected: all tests pass (count depends on prior tasks; should be ~30+ tests).

- [ ] **Step 6: Commit**

```bash
git add pipeline/stages.py tests/test_stages.py
git commit -m "Add DB-aware stage runners (discover/crawl/rescue/extract)"
```

---

## Task 14: Directory scrapers (Grounded Solutions, Center for CLT)

The two directory pages may be JS-rendered, paywalled, or behind anti-bot protection. We approach them carefully: **fetch manually first, capture the HTML as a fixture, then write a parser against the fixture.** If a directory turns out to be blocked or fully JS, document the fallback (manual CSV import) in this task and keep moving.

**Files:**
- Modify: `pipeline/seeds.py`
- Modify: `tests/test_seeds.py`
- Create: `tests/fixtures/grounded_solutions.html`
- Create: `tests/fixtures/center_clt.html`

- [ ] **Step 1: Manually capture the Grounded Solutions member directory**

Run:
```bash
source .venv/Scripts/activate
python -c "import requests; r=requests.get('https://groundedsolutions.org/tools-for-success/membership-directory', headers={'User-Agent':'MontavillaCLT-Inventory/1.0 (research; tfalcon@sfwconstruction.com)'}, timeout=20); print(r.status_code); open('tests/fixtures/grounded_solutions.html','w',encoding='utf-8').write(r.text)"
```

Expected: status code 200; fixture file written.

If status is not 200, or the saved file is mostly empty / contains only `<script>` tags (i.e. JS-rendered), STOP. Update this task with `STATUS: blocked — directory requires JS render` and skip to Step 5 (manual-CSV fallback). The pipeline still works without the directory; state-by-state SerpAPI sweep + the existing JSON cover most of the inventory.

- [ ] **Step 2: Inspect the fixture HTML and identify the listing selector**

Open `tests/fixtures/grounded_solutions.html`. Grep for several known member names (e.g., "Proud Ground", "Sabin CDC", "Champlain Housing Trust") to locate listing markup. Identify:

1. The CSS selector for the repeating member-listing element.
2. The selector for the member name inside one listing.
3. The selectors for city, state, and website if present.

When you implement Step 4, use the selectors you identified here, replacing the example selectors in the parser code below. The example selectors are common defaults that may or may not match this specific page — verify against the fixture before assuming they work.

- [ ] **Step 3: Add a focused test against a small slice of the fixture**

Append to `tests/test_seeds.py`:
```python
from pathlib import Path
from pipeline.seeds import parse_grounded_solutions

GS_FIXTURE = Path(__file__).parent / "fixtures" / "grounded_solutions.html"


def test_parse_grounded_solutions_extracts_at_least_50_entries():
    if not GS_FIXTURE.exists():
        import pytest; pytest.skip("fixture not present (directory blocked at capture time)")
    rows = parse_grounded_solutions(GS_FIXTURE.read_text(encoding="utf-8"))
    assert len(rows) >= 50
    sample = rows[0]
    assert sample["source"] == "grounded-solutions"
    assert sample["status"] in ("discovered", "url_found")
    assert sample["state"] and len(sample["state"]) == 2
    assert sample["name"]
```

- [ ] **Step 4: Implement `parse_grounded_solutions` in `pipeline/seeds.py`**

Append to `pipeline/seeds.py` — parser whose selectors match what you found in Step 2:
```python
from bs4 import BeautifulSoup


def parse_grounded_solutions(html: str) -> list[dict]:
    """Extract CLT rows from the Grounded Solutions Network member directory page.

    Selectors are filled in based on the captured fixture (see Task 14 step 2).
    The parser is defensive: missing fields → None.
    """
    soup = BeautifulSoup(html, "lxml")
    rows: list[dict] = []
    for card in soup.select("div.member-card, article.member"):
        name_el = card.select_one(".member-name, h3, h2")
        city_el = card.select_one(".member-city, .city")
        state_el = card.select_one(".member-state, .state")
        url_el = card.select_one("a[href^='http']")
        if not name_el:
            continue
        name = name_el.get_text(strip=True)
        state = (state_el.get_text(strip=True) if state_el else "")[:2].upper() or None
        url = url_el["href"] if url_el else None
        rows.append({
            "id": slugify(name),
            "name": name,
            "city": city_el.get_text(strip=True) if city_el else None,
            "state": state,
            "url": url,
            "source": "grounded-solutions",
            "status": "url_found" if url else "discovered",
            "notes": None,
        })
    return rows
```

The example selectors above (`div.member-card`, `.member-name`, etc.) are common patterns. Replace each with the selector you identified in Step 2 before running the test.

- [ ] **Step 5: Run the test**

```bash
python -m pytest tests/test_seeds.py -k grounded_solutions -v
```

Expected: pass (or skip if Step 1 was blocked). If it fails because the parser found < 50 entries, revisit selectors.

- [ ] **Step 6a: Find and capture the Center for CLT & Cooperative Innovation directory**

The Center for CLT & Cooperative Innovation (formerly NACLI) hosts a member directory. URLs change; first verify the current directory URL with a SerpAPI query or a manual web search for `"Center for Community Land Trust" OR "NACLI" member directory`.

Once you have the URL, capture the HTML:
```bash
source .venv/Scripts/activate
python -c "import requests; URL='<paste-url-here>'; r=requests.get(URL, headers={'User-Agent':'MontavillaCLT-Inventory/1.0 (research; tfalcon@sfwconstruction.com)'}, timeout=20); print(r.status_code); open('tests/fixtures/center_clt.html','w',encoding='utf-8').write(r.text)"
```

Same blocked-rule as Step 1: if the response is JS-rendered or non-200, mark blocked and skip to Step 7.

- [ ] **Step 6b: Identify the listing selector in the Center for CLT fixture**

Same approach as Step 2: open the fixture, locate the repeating member listing, identify name/city/state/url selectors. Use these in the parser code in Step 6d.

- [ ] **Step 6c: Add a test for `parse_center_clt`**

Append to `tests/test_seeds.py`:
```python
from pipeline.seeds import parse_center_clt

CC_FIXTURE = Path(__file__).parent / "fixtures" / "center_clt.html"


def test_parse_center_clt_extracts_at_least_30_entries():
    if not CC_FIXTURE.exists():
        import pytest; pytest.skip("fixture not present (directory blocked at capture time)")
    rows = parse_center_clt(CC_FIXTURE.read_text(encoding="utf-8"))
    assert len(rows) >= 30
    sample = rows[0]
    assert sample["source"] == "center-clt-innovation"
    assert sample["status"] in ("discovered", "url_found")
    assert sample["name"]
```

- [ ] **Step 6d: Implement `parse_center_clt`**

Append to `pipeline/seeds.py`:
```python
def parse_center_clt(html: str) -> list[dict]:
    """Extract CLT rows from the Center for CLT & Cooperative Innovation directory.

    Selectors are filled in based on the captured fixture (see Task 14 step 6b).
    """
    soup = BeautifulSoup(html, "lxml")
    rows: list[dict] = []
    for card in soup.select("div.directory-entry, li.member, article.member"):
        name_el = card.select_one("h3, h2, .name")
        city_el = card.select_one(".city, .location")
        state_el = card.select_one(".state")
        url_el = card.select_one("a[href^='http']")
        if not name_el:
            continue
        name = name_el.get_text(strip=True)
        rows.append({
            "id": slugify(name),
            "name": name,
            "city": city_el.get_text(strip=True) if city_el else None,
            "state": (state_el.get_text(strip=True) if state_el else "")[:2].upper() or None,
            "url": url_el["href"] if url_el else None,
            "source": "center-clt-innovation",
            "status": "url_found" if url_el else "discovered",
            "notes": None,
        })
    return rows
```

Replace the example selectors with the ones you identified in Step 6b.

- [ ] **Step 6e: Run the test**

```bash
python -m pytest tests/test_seeds.py -k center_clt -v
```

Expected: pass (or skip if Step 6a was blocked).

- [ ] **Step 7: Add a manual-CSV seed function as the universal fallback**

Append to `pipeline/seeds.py`:
```python
import csv


def parse_manual_csv(csv_path: Path) -> list[dict]:
    """Read a manually-curated CSV with columns: name, city, state, url (url optional).

    Used when a third-party directory is JS-rendered or blocked. The user
    drops a CSV into data/seed/<source>.csv and points this function at it.
    """
    rows: list[dict] = []
    with Path(csv_path).open(newline="", encoding="utf-8") as f:
        for entry in csv.DictReader(f):
            name = (entry.get("name") or "").strip()
            if not name:
                continue
            url = (entry.get("url") or "").strip() or None
            rows.append({
                "id": slugify(name),
                "name": name,
                "city": (entry.get("city") or "").strip() or None,
                "state": (entry.get("state") or "").strip().upper()[:2] or None,
                "url": url,
                "source": "manual-csv",
                "status": "url_found" if url else "discovered",
                "notes": None,
            })
    return rows
```

- [ ] **Step 8: Add a test for `parse_manual_csv`**

Append to `tests/test_seeds.py`:
```python
def test_parse_manual_csv(tmp_path):
    p = tmp_path / "seed.csv"
    p.write_text("name,city,state,url\nFoo CLT,Olympia,WA,https://foo.org\nBar CLT,Bend,OR,\n")
    rows = parse_manual_csv(p)
    assert rows[0]["url"] == "https://foo.org"
    assert rows[0]["status"] == "url_found"
    assert rows[1]["url"] is None
    assert rows[1]["status"] == "discovered"

# Add to imports at top of file:
from pipeline.seeds import parse_manual_csv
```

- [ ] **Step 9: Run all seed tests**

```bash
python -m pytest tests/test_seeds.py -v
```

Expected: all pass (or directory tests skip if blocked).

- [ ] **Step 10: Commit**

```bash
git add pipeline/seeds.py tests/test_seeds.py tests/fixtures/grounded_solutions.html tests/fixtures/center_clt.html
git commit -m "Add Grounded Solutions + Center for CLT directory parsers and CSV fallback"
```

---

## Task 15: Notebook orchestrator

**Files:**
- Create: `notebooks/run_pipeline.ipynb`

The notebook is a thin orchestrator. Each cell runs one stage and prints a summary. We create the notebook by writing the JSON directly because it's small and simple.

- [ ] **Step 1: Create `notebooks/run_pipeline.ipynb`**

```json
{
 "cells": [
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "# CLT Inventory Pipeline\n",
    "\n",
    "Run cells top-to-bottom. Each stage is idempotent — re-running a cell is safe.\n",
    "\n",
    "**Prereqs:** `.env` with `DATABASE_URL` and `SERPAPI_KEY`; `pip install -r requirements.txt` in the activated venv."
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": ["## 0. Bootstrap schema (idempotent)"]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "from pipeline import db\n",
    "db.bootstrap_schema()\n",
    "print('schema ready')"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": ["## 1. Seed from existing clts.json"]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "from pipeline.config import SITE_CLTS_JSON\n",
    "from pipeline.seeds import parse_existing_clts\n",
    "from pipeline.stages import upsert_clts\n",
    "\n",
    "rows = parse_existing_clts(SITE_CLTS_JSON)\n",
    "upsert_clts(rows)\n",
    "print(f'seeded {len(rows)} from existing clts.json')"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## 2. Seed from directories\n",
    "\n",
    "Skip the directory you couldn't capture during Task 14; the rest of the pipeline still works."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "from pathlib import Path\n",
    "from pipeline.seeds import parse_grounded_solutions, parse_center_clt\n",
    "from pipeline.stages import upsert_clts\n",
    "\n",
    "for fixture, parser in [\n",
    "    (Path('tests/fixtures/grounded_solutions.html'), parse_grounded_solutions),\n",
    "    (Path('tests/fixtures/center_clt.html'), parse_center_clt),\n",
    "]:\n",
    "    if not fixture.exists():\n",
    "        print(f'skipping {fixture.name} (no fixture)')\n",
    "        continue\n",
    "    rows = parser(fixture.read_text(encoding='utf-8'))\n",
    "    upsert_clts(rows)\n",
    "    print(f'{fixture.name}: seeded {len(rows)}')"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": ["## 3. State-by-state SerpAPI sweep"]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "from pipeline.config import load_env\n",
    "from pipeline.serpapi import SerpApiClient, PostgresCache\n",
    "from pipeline.seeds import US_STATES, build_state_sweep_query, parse_state_sweep_results\n",
    "from pipeline.stages import upsert_clts\n",
    "\n",
    "client = SerpApiClient(api_key=load_env()['SERPAPI_KEY'], cache=PostgresCache())\n",
    "total = 0\n",
    "for state in US_STATES:\n",
    "    payload = client.search(build_state_sweep_query(state))\n",
    "    rows = parse_state_sweep_results(payload, state=state)\n",
    "    if rows:\n",
    "        upsert_clts(rows)\n",
    "        total += len(rows)\n",
    "    print(f'{state}: {len(rows)} candidates')\n",
    "print(f'total swept: {total}')"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": ["## 4. Discover URLs for CLTs without one"]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "from pipeline.stages import run_discover\n",
    "print(run_discover())"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": ["## 5. Crawl"]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "from pipeline.stages import run_crawl\n",
    "print(run_crawl())"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": ["## 6. Rescue dead/parked sites"]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "from pipeline.stages import run_rescue, run_crawl\n",
    "print(run_rescue())\n",
    "print(run_crawl())  # crawl any URLs the rescue moved back to 'url_found'"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": ["## 7. Extract emails"]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "from pipeline.stages import run_extract\n",
    "print(run_extract())"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": ["## 8. Diagnostics"]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "from pipeline.db import connect\n",
    "with connect() as conn, conn.cursor() as cur:\n",
    "    cur.execute('SELECT status, count(*) FROM inv_clts GROUP BY status ORDER BY 2 DESC')\n",
    "    print('CLT status distribution:')\n",
    "    for status, n in cur.fetchall():\n",
    "        print(f'  {status:20s} {n}')\n",
    "    cur.execute('SELECT error, count(*) FROM inv_pages WHERE error IS NOT NULL GROUP BY error ORDER BY 2 DESC LIMIT 10')\n",
    "    print('\\nTop crawl errors:')\n",
    "    for err, n in cur.fetchall():\n",
    "        print(f'  {n:5d} {err}')\n",
    "    cur.execute('SELECT count(DISTINCT clt_id) FROM inv_emails')\n",
    "    print(f'\\nCLTs with at least one email: {cur.fetchone()[0]}')"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## 9. Export to src/data/clts.json (opt-in)\n",
    "\n",
    "This is the only cell that writes back into the site repo. Run it when you're satisfied with the inventory."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "from pipeline.export import export_to_clts_json\n",
    "summary = export_to_clts_json(dry_run=True)\n",
    "print('dry-run:', summary)\n",
    "# When ready, change to dry_run=False:\n",
    "# print(export_to_clts_json(dry_run=False))"
   ]
  }
 ],
 "metadata": {
  "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
  "language_info": {"name": "python", "version": "3.11"}
 },
 "nbformat": 4,
 "nbformat_minor": 5
}
```

- [ ] **Step 2: Smoke test that the notebook is valid JSON and Jupyter can open it**

```bash
source .venv/Scripts/activate
python -c "import nbformat; nb = nbformat.read('notebooks/run_pipeline.ipynb', as_version=4); print(f'cells: {len(nb.cells)}')"
```

Expected: `cells: 19` (or similar — confirms valid notebook).

- [ ] **Step 3: Run the bootstrap cell end-to-end against real Neon**

Launch Jupyter Lab:
```bash
source .venv/Scripts/activate
jupyter lab notebooks/run_pipeline.ipynb
```

Run cell 0 (schema bootstrap) and cell 1 (seed from existing JSON). Verify output:
- Cell 0: `schema ready`
- Cell 1: `seeded 33 from existing clts.json`

Then in a SQL client (or another notebook cell), confirm:
```sql
SELECT count(*) FROM inv_clts WHERE source = 'existing';
-- expected: 33
```

- [ ] **Step 4: Commit**

```bash
git add notebooks/run_pipeline.ipynb
git commit -m "Add Jupyter orchestrator notebook for the inventory pipeline"
```

---

## Task 16: End-to-end smoke run

This is the integration test. Run the full notebook against the real Neon DB and SerpAPI account.

- [ ] **Step 1: Run cell 0 (schema bootstrap)**

Already verified in Task 15 — should be a no-op now.

- [ ] **Step 2: Run cell 1 (seed from existing JSON)**

Already verified in Task 15.

- [ ] **Step 3: Run cell 2 (directory scrapers) if applicable**

Skip silently if fixtures aren't present.

- [ ] **Step 4: Run cell 3 (state sweep)**

Watch the per-state output. Expect ~5-15 candidates per state. Total runtime ≈ 50 states × ~2-3s SerpAPI latency ≈ 2-3 minutes. Expect ~150-400 new CLT candidates.

- [ ] **Step 5: Run cell 4 (URL discovery)**

For any CLT still without a URL after sweep+seed. Expect this to be a small set (most state-sweep results already have URLs).

- [ ] **Step 6: Run cell 5 (crawl)**

This is the longest cell — ~300 sites × ~3 pages × ~2s avg ≈ 30 minutes. Watch the per-CLT progress. Expect ~80-90% success rate.

- [ ] **Step 7: Run cell 6 (rescue)**

Re-queries the failures, re-crawls any that found new URLs. Expect to recover 10-30% of the failures.

- [ ] **Step 8: Run cell 7 (extract emails)**

Fast — purely local processing of stored HTML. Expect 1-3 emails per successfully crawled site, with maybe 50-70% of crawled sites producing at least one email.

- [ ] **Step 9: Run cell 8 (diagnostics)**

Check the status distribution. If `crawl_failed` is unexpectedly high, dig into `inv_pages.error`. If `url_not_found` is high, the discovery heuristic may be too strict — capture a few examples and adjust `is_plausible_clt_domain` blocklist or token rules.

- [ ] **Step 10: Manual review of diagnostic output**

Spot-check 5 random CLTs with `status='extracted'`:
```sql
SELECT c.id, c.name, c.url, count(e.id) AS emails
FROM inv_clts c LEFT JOIN inv_emails e ON e.clt_id = c.id
WHERE c.status = 'extracted'
GROUP BY c.id ORDER BY random() LIMIT 5;
```
Open each CLT's URL in a browser, confirm the emails we extracted look right.

- [ ] **Step 11: Run cell 9 (export, dry-run)**

Confirm the summary makes sense (existing_preserved=33, new=N where N is roughly your sweep+directory yield, total=33+N).

- [ ] **Step 12: Decide whether to flip to `dry_run=False`**

Show the diagnostic output and dry-run summary to the user. They confirm before the export writes `src/data/clts.json`.

- [ ] **Step 13: Commit the regenerated `clts.json`**

After the user approves the export and runs the cell with `dry_run=False`:
```bash
cd C:/Users/tfalcon/montavilla-clt
git add src/data/clts.json
git commit -m "Regenerate clts.json from CLT inventory pipeline"
```

---

## Done

The pipeline is shipped when:
- All unit tests pass.
- The notebook runs cleanly end-to-end against real Neon + SerpAPI.
- `inv_clts.status` distribution shows >80% in `crawled` or `extracted`.
- `src/data/clts.json` has been regenerated and the site map shows the expanded inventory.

Out-of-scope follow-ups (separate plans):
- LLM classification of `axes` / `focus` from crawled HTML.
- Staff/board name and role extraction.
- Phone numbers, addresses, social handles.
- Outreach UI built on top of `inv_emails`.
