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
            "email": "private@a.org"}]
    merged = merge_with_existing(inv, [])
    assert "email" not in merged[0]


def test_existing_entry_without_url_is_preserved():
    """Hand-curated entries with url=null must survive the export — no data loss."""
    existing = [{
        "id": "rootedhomes", "name": "RootedHomes", "location": "Bend, OR",
        "state": "OR", "founded": 2015, "focus": ["housing"],
        "axes": {"housing": 94, "agriculture": 4, "commercial": 2},
        "url": None, "scale": "~12 homes, 3 communities",
        "notes": "Sustainable and permanently affordable housing in Central Oregon",
    }]
    # inv_clts row mirrors the existing entry (same id, url=None from parse_existing_clts)
    inv = [{"id": "rootedhomes", "name": "RootedHomes", "city": "Bend",
            "state": "OR", "url": None, "notes": None}]
    merged = merge_with_existing(inv, existing)
    assert len(merged) == 1
    assert merged[0] == existing[0]


def test_existing_entry_absent_from_inv_rows_still_preserved():
    """If the DB hasn't been seeded yet, existing entries must not vanish."""
    existing = [{
        "id": "proud-ground", "name": "Proud Ground", "location": "Portland, OR",
        "state": "OR", "url": "https://www.proudground.org",
        "founded": 1999, "focus": ["housing"], "axes": {}, "scale": "x", "notes": "y",
    }]
    merged = merge_with_existing(inv_rows=[], existing=existing)
    assert merged == existing
