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
    assert not any("nytimes" in (r.get("url") or "") for r in rows)


def test_parse_state_sweep_preserves_hyphenated_names():
    payload = {"organic_results": [
        {"title": "Thistle Housing-ABQ | Affordable Homes", "link": "https://thistlehousing.org/"},
    ]}
    rows = parse_state_sweep_results(payload, state="NM")
    assert len(rows) == 1
    assert rows[0]["name"] == "Thistle Housing-ABQ"


GS_FIXTURE = Path(__file__).parent / "fixtures" / "grounded_solutions.html"
CC_FIXTURE = Path(__file__).parent / "fixtures" / "center_clt.html"


def test_parse_grounded_solutions_extracts_at_least_50_entries():
    from pipeline.seeds import parse_grounded_solutions
    if not GS_FIXTURE.exists():
        import pytest; pytest.skip("fixture not present (directory blocked at capture time)")
    rows = parse_grounded_solutions(GS_FIXTURE.read_text(encoding="utf-8"))
    assert len(rows) >= 50
    sample = rows[0]
    assert sample["source"] == "grounded-solutions"
    assert sample["status"] in ("discovered", "url_found")
    assert sample["state"] and len(sample["state"]) == 2
    assert sample["name"]


def test_parse_center_clt_extracts_at_least_30_entries():
    from pipeline.seeds import parse_center_clt
    if not CC_FIXTURE.exists():
        import pytest; pytest.skip("fixture not present (directory blocked at capture time)")
    rows = parse_center_clt(CC_FIXTURE.read_text(encoding="utf-8"))
    assert len(rows) >= 30
    sample = rows[0]
    assert sample["source"] == "center-clt-innovation"
    assert sample["status"] in ("discovered", "url_found")
    assert sample["name"]


def test_parse_manual_csv(tmp_path):
    from pipeline.seeds import parse_manual_csv
    p = tmp_path / "seed.csv"
    p.write_text("name,city,state,url\nFoo CLT,Olympia,WA,https://foo.org\nBar CLT,Bend,OR,\n")
    rows = parse_manual_csv(p)
    assert rows[0]["url"] == "https://foo.org"
    assert rows[0]["status"] == "url_found"
    assert rows[1]["url"] is None
    assert rows[1]["status"] == "discovered"


def test_parse_manual_csv_accepts_full_state_names():
    from pipeline.seeds import parse_manual_csv
    import tempfile, os
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8", newline="") as f:
        f.write("name,city,state,url\nVirginia CLT,Richmond,Virginia,https://v.org\nMT CLT,Helena,Montana,https://m.org\nShort CLT,X,OR,https://s.org\n")
        path = f.name
    try:
        rows = parse_manual_csv(Path(path))
        state_by_name = {r["name"]: r["state"] for r in rows}
        assert state_by_name["Virginia CLT"] == "VA"
        assert state_by_name["MT CLT"] == "MT"
        assert state_by_name["Short CLT"] == "OR"
    finally:
        os.unlink(path)


def test_parse_manual_csv_strips_utf8_bom_from_excel_exports():
    from pipeline.seeds import parse_manual_csv
    import tempfile, os
    # Excel's "Save As CSV UTF-8" writes a BOM. Without utf-8-sig, every row is dropped.
    with tempfile.NamedTemporaryFile(mode="wb", suffix=".csv", delete=False) as f:
        f.write(b"\xef\xbb\xbf")  # UTF-8 BOM
        f.write(b"name,city,state,url\n")
        f.write(b"Foo CLT,Olympia,WA,https://foo.org\n")
        path = f.name
    try:
        rows = parse_manual_csv(Path(path))
        assert len(rows) == 1
        assert rows[0]["name"] == "Foo CLT"
        assert rows[0]["state"] == "WA"
    finally:
        os.unlink(path)
