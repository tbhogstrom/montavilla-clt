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
