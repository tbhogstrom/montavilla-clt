"""Seed candidate CLTs from existing JSON and SerpAPI state sweeps."""
from __future__ import annotations

import csv
import json
import re
import unicodedata
from pathlib import Path

from bs4 import BeautifulSoup

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


def parse_grounded_solutions(html: str) -> list[dict]:
    """Extract CLT rows from the Grounded Solutions Network member directory page.

    Defensive selectors — the live page is JS-rendered so the static HTML has no
    member data. Returns empty list in that case; implementation is kept so that
    a future fixture (e.g., from a headless-browser capture) can be parsed without
    code changes. Manual-CSV seeding (parse_manual_csv) is the recommended path.
    """
    soup = BeautifulSoup(html, "html.parser")
    rows: list[dict] = []
    for card in soup.select("div.member-card, article.member, li.member"):
        name_el = card.select_one(".member-name, h3, h2, .name")
        city_el = card.select_one(".member-city, .city, .location")
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


def parse_center_clt(html: str) -> list[dict]:
    """Extract CLT rows from the Center for CLT & Cooperative Innovation directory.

    Same caveat as parse_grounded_solutions — page is JS-rendered, parser is a
    placeholder that exercises a set of plausible selectors.
    """
    soup = BeautifulSoup(html, "html.parser")
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


_STATE_NAME_TO_CODE = {v.upper(): k for k, v in US_STATES.items()}


def _normalize_state(raw: str) -> str | None:
    """Accept 'OR', 'or', 'Oregon', 'OREGON' → 'OR'. Returns None for blank input."""
    s = (raw or "").strip().upper()
    if not s:
        return None
    if s in US_STATES:
        return s
    if s in _STATE_NAME_TO_CODE:
        return _STATE_NAME_TO_CODE[s]
    return s[:2] or None


def parse_manual_csv(csv_path: Path) -> list[dict]:
    """Read a manually-curated CSV with columns: name, city, state, url (url optional).

    Used when a third-party directory is JS-rendered or blocked. The user
    drops a CSV into data/seed/<source>.csv and points this function at it.

    ``encoding="utf-8-sig"`` handles the BOM that Excel writes by default when
    saving as UTF-8 CSV.
    """
    rows: list[dict] = []
    with Path(csv_path).open(newline="", encoding="utf-8-sig") as f:
        for entry in csv.DictReader(f):
            name = (entry.get("name") or "").strip()
            if not name:
                continue
            url = (entry.get("url") or "").strip() or None
            rows.append({
                "id": slugify(name),
                "name": name,
                "city": (entry.get("city") or "").strip() or None,
                "state": _normalize_state(entry.get("state") or ""),
                "url": url,
                "source": "manual-csv",
                "status": "url_found" if url else "discovered",
                "notes": None,
            })
    return rows


def parse_freddie_mac(html: str) -> list[dict]:
    """Parse the Freddie Mac CLT database table at sf.freddiemac.com/general/fre-clt-database.

    The page renders one <table> with columns: CLT Name, Address, Contact, County, State,
    Ground Lease Type. Address is a concatenated string like "123 Main St.City, ST 12345";
    we don't try to split it — we only use it as a city/location hint. The CLT's website is
    NOT listed here, so returned rows have url=None and status='discovered' — the pipeline's
    discover stage will resolve URLs.
    """
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table")
    if table is None:
        return []
    rows: list[dict] = []
    trs = table.find_all("tr")
    for tr in trs[1:]:  # skip header
        cells = [c.get_text(strip=True) for c in tr.find_all(["td", "th"])]
        if len(cells) < 5:
            continue
        name = cells[0]
        address = cells[1]
        state = cells[4][:2].upper() if len(cells) > 4 else ""
        if not name or not state:
            continue
        # Address format is "123 Main St.City, ST 12345" — extract the city by grabbing
        # the segment before the last comma before the state code.
        city = None
        if "," in address:
            before_comma = address.rsplit(",", 1)[0]
            # Take the final uppercase-initial word cluster; imprecise but acceptable.
            parts = re.split(r"(?<=[a-z])(?=[A-Z])", before_comma)
            city = parts[-1].strip() or None
        notes = f"Freddie Mac CLT Database: {cells[5]}" if len(cells) >= 6 and cells[5] else None
        rows.append({
            "id": slugify(name),
            "name": name,
            "city": city,
            "state": state,
            "url": None,
            "source": "freddie-mac",
            "status": "discovered",
            "notes": notes,
        })
    return rows
