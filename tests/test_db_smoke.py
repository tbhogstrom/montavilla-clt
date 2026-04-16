"""Smoke test: bootstrap schema, insert a temp row, read it back, clean up.

Skipped when DATABASE_URL is not configured. This is the only test that
hits a real database.
"""
import pytest

from pipeline import db

try:
    from pipeline.config import load_env
    DB_URL = load_env().get("DATABASE_URL")
except RuntimeError:
    DB_URL = None

pytestmark = pytest.mark.skipif(
    not DB_URL, reason="DATABASE_URL not set; skipping live-DB smoke test"
)

EXPECTED_TABLES = {"inv_clts", "inv_pages", "inv_emails", "inv_serpapi_cache"}


def test_bootstrap_and_roundtrip():
    db.bootstrap_schema()
    with db.connect() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = 'public' AND table_name LIKE 'inv_%'"
        )
        tables = {r[0] for r in cur.fetchall()}
        assert EXPECTED_TABLES <= tables, f"missing tables: {EXPECTED_TABLES - tables}"

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
