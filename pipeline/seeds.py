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


_TITLE_TRIM = re.compile(r"\s+[-–·•|].*$")


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
