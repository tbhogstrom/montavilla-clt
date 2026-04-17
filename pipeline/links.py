"""Find and classify contact-like links on a CLT homepage."""
from __future__ import annotations

import re
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from pipeline.config import MAX_CONTACT_LINKS

KIND_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("contact", re.compile(r"contact", re.I)),
    ("staff", re.compile(r"staff", re.I)),
    ("board", re.compile(r"board", re.I)),
    ("team", re.compile(r"team", re.I)),
    ("about", re.compile(r"about", re.I)),
]


def classify_page_kind(href: str, link_text: str) -> str | None:
    """Return one of contact/staff/board/team/about, or None if no match."""
    for kind, pat in KIND_PATTERNS:
        if pat.search(href):
            return kind
    for kind, pat in KIND_PATTERNS:
        if pat.search(link_text or ""):
            return kind
    return None


def _same_host(a: str, b: str) -> bool:
    ha = urlparse(a).hostname
    hb = urlparse(b).hostname
    return ha is not None and ha.lower() == (hb or "").lower()


def find_contact_links(html: str, base_url: str) -> list[tuple[str, str]]:
    """Return up to MAX_CONTACT_LINKS (url, page_kind) tuples, deduped."""
    soup = BeautifulSoup(html, "html.parser")
    seen: dict[str, str] = {}
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if not href or href.startswith("#") or href.startswith("mailto:") or href.startswith("javascript:"):
            continue
        full = urljoin(base_url, href)
        if not _same_host(full, base_url):
            continue
        kind = classify_page_kind(href, a.get_text(strip=True))
        if kind is None:
            continue
        full = full.split("#", 1)[0]
        if full in seen:
            continue
        seen[full] = kind
        if len(seen) >= MAX_CONTACT_LINKS:
            break
    return list(seen.items())
