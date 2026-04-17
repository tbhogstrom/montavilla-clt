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
    """Preserve all existing hand-curated entries; add new rows only when they have a URL.

    Existing entries are kept verbatim whether or not the corresponding inv_clts
    row has a url — this protects hand-curated entries (axes, scale, notes) for
    CLTs we know about but haven't resolved a live website for yet.
    """
    by_id = {e["id"]: e for e in existing}
    out: list[dict] = []
    seen_ids: set[str] = set()
    for row in inv_rows:
        if row["id"] in by_id:
            out.append(by_id[row["id"]])
            seen_ids.add(row["id"])
        elif row.get("url"):
            out.append(default_new_entry(row))
            seen_ids.add(row["id"])
    # Preserve existing entries that weren't surfaced by the current inv_clts query.
    for entry in existing:
        if entry["id"] not in seen_ids:
            out.append(entry)
    out.sort(key=lambda e: ((e.get("state") or "").lower(), e["name"].lower()))
    return out


def export_to_clts_json(*, dry_run: bool = False) -> dict:
    """Pull inv_clts → merge with existing clts.json → write. Returns summary dict."""
    with connect() as conn, conn.cursor() as cur:
        cur.execute("SELECT id, name, city, state, url, notes FROM inv_clts")
        inv_rows = [
            {"id": r[0], "name": r[1], "city": r[2], "state": r[3], "url": r[4], "notes": r[5]}
            for r in cur.fetchall()
        ]
    existing_path = Path(SITE_CLTS_JSON)
    existing = json.loads(existing_path.read_text(encoding="utf-8")) if existing_path.exists() else []
    existing_ids = {e["id"] for e in existing}
    merged = merge_with_existing(inv_rows, existing)

    inv_ids = {r["id"] for r in inv_rows}
    summary = {
        "existing_preserved": sum(1 for e in merged if e["id"] in existing_ids),
        "new": sum(1 for e in merged if e["id"] not in existing_ids),
        "total": len(merged),
        "skipped_no_url": sum(1 for r in inv_rows if not r.get("url") and r["id"] not in existing_ids),
    }
    if not dry_run:
        existing_path.write_text(
            json.dumps(merged, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    return summary
