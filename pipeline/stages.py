"""DB-aware stage runners. Each function picks up its work from inv_clts.status."""
from __future__ import annotations

from pathlib import Path

from pipeline.config import HTML_DIR, load_env
from pipeline.crawler import crawl_one
from pipeline.db import connect
from pipeline.discover import discover_url, pick_best_url
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
ON CONFLICT (clt_id, page_id, email, source) DO NOTHING
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
        q_parts = [f'"{name}"']
        if city:
            q_parts.append(city)
        if state:
            q_parts.append(state)
        data = client.search(" ".join(q_parts))
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
        else:
            # No fresh URL found — move to a terminal status so rescue doesn't re-pick this row.
            with connect() as conn, conn.cursor() as cur:
                cur.execute(
                    "UPDATE inv_clts SET status = 'rescue_failed', updated_at = now() "
                    "WHERE id = %s",
                    (clt_id,),
                )
                conn.commit()
    return {"checked": len(rows), "rescued": rescued}


def run_extract() -> dict:
    """For each inv_clts.status='crawled', extract emails from stored HTML.

    Opens one connection per CLT covering all of its pages, all email inserts,
    and the terminal status update — keeps connection count bounded and makes
    each CLT's extraction atomic.
    """
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
                    cur.execute(email_insert_sql(), {
                        "clt_id": clt_id,
                        "page_id": page_id,
                        "email": e["email"],
                        "source": e["source"],
                        "context": e["context"],
                    })
                    clt_emails += 1
            cur.execute(
                "UPDATE inv_clts SET status = 'extracted', updated_at = now() WHERE id = %s",
                (clt_id,),
            )
            conn.commit()
        n_clts += 1
        n_emails += clt_emails
    return {"clts": n_clts, "emails_inserted": n_emails}
