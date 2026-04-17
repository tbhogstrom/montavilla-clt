"""Tests for pipeline.seeds — slug, parse-existing, state-sweep helpers."""
import json

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
