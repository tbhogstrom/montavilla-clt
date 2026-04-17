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
  extracted_at    timestamptz NOT NULL DEFAULT now(),
  UNIQUE (clt_id, page_id, email, source)
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


_DSN: str | None = None


def _dsn() -> str:
    """Resolve DATABASE_URL once per process and cache it."""
    global _DSN
    if _DSN is None:
        _DSN = load_env()["DATABASE_URL"]
    return _DSN


@contextlib.contextmanager
def connect() -> Iterator[psycopg.Connection]:
    """Yield a psycopg connection using DATABASE_URL from .env (cached)."""
    conn = psycopg.connect(_dsn())
    try:
        yield conn
    finally:
        conn.close()


def bootstrap_schema() -> None:
    """Idempotently create inv_* tables and indexes."""
    with connect() as conn, conn.cursor() as cur:
        cur.execute(SCHEMA_SQL)
        conn.commit()
