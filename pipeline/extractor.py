"""Email extraction from stored HTML.

Three sources, in order of confidence: mailto: links, visible-text regex,
deobfuscated patterns. All results are normalized and filtered against a
domain blocklist before return.
"""
from __future__ import annotations

import re
from typing import Iterable

from bs4 import BeautifulSoup

EMAIL_RE = re.compile(
    r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b"
)

DEOBFUSCATE_RE = re.compile(
    r"\b([A-Za-z0-9._%+\-]+)\s*[\[\(]?\s*(?:at|@)\s*[\]\)]?\s*"
    r"([A-Za-z0-9.\-]+)\s+[\[\(]?\s*dot\s*[\]\)]?\s+"
    r"([A-Za-z]{2,})\b",
    re.IGNORECASE,
)

BLOCKED_EMAIL_DOMAINS = {
    "example.com", "example.org", "example.net",
    "sentry.io",
    "wixpress.com",
    "squarespace.com",
    "wordpress.com",
    "godaddy.com",
    "domain.com",
    "yourdomain.com",
    "test.com",
}

CONTEXT_RADIUS = 100
MAX_SNIPPET = 200


def normalize_email(raw: str) -> str:
    # Strip NUL bytes — Postgres text columns reject them.
    return raw.replace("\x00", "").strip().rstrip(".,;:").lower()


def _domain(email: str) -> str:
    return email.rsplit("@", 1)[-1]


def _is_blocked(email: str) -> bool:
    d = _domain(email)
    if d in BLOCKED_EMAIL_DOMAINS:
        return True
    return any(d.endswith("." + base) for base in BLOCKED_EMAIL_DOMAINS)


def _snippet(text: str, start: int, end: int) -> str:
    lo = max(0, start - CONTEXT_RADIUS)
    hi = min(len(text), end + CONTEXT_RADIUS)
    # Strip NUL bytes (some pages embed them in noise); Postgres text rejects 0x00.
    return text[lo:hi].replace("\x00", "").replace("\n", " ").strip()[:MAX_SNIPPET]


def extract_emails(html: str) -> list[dict]:
    """Return a list of {email, source, context} dicts. Deduped by (email, source)."""
    soup = BeautifulSoup(html, "html.parser")
    found: dict[tuple[str, str], dict] = {}

    # 1) mailto: links
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if href.lower().startswith("mailto:"):
            raw = href.split(":", 1)[1].split("?", 1)[0]
            email = normalize_email(raw)
            if EMAIL_RE.fullmatch(email) and not _is_blocked(email):
                key = (email, "mailto")
                found.setdefault(key, {
                    "email": email, "source": "mailto",
                    "context": a.get_text(strip=True) or email,
                })

    # 2) visible text — strip script/style noise
    for tag in soup(["script", "style"]):
        tag.decompose()
    text = soup.get_text(" ", strip=False)

    for m in EMAIL_RE.finditer(text):
        email = normalize_email(m.group(0))
        if _is_blocked(email):
            continue
        key = (email, "text")
        if key in found:
            continue
        found.setdefault(key, {
            "email": email, "source": "text",
            "context": _snippet(text, m.start(), m.end()),
        })

    # 3) deobfuscated
    for m in DEOBFUSCATE_RE.finditer(text):
        local, host, tld = m.group(1), m.group(2), m.group(3)
        candidate = normalize_email(f"{local}@{host}.{tld}")
        if not EMAIL_RE.fullmatch(candidate) or _is_blocked(candidate):
            continue
        key = (candidate, "deobfuscated")
        if key in found or (candidate, "text") in found or (candidate, "mailto") in found:
            continue
        found[key] = {
            "email": candidate, "source": "deobfuscated",
            "context": _snippet(text, m.start(), m.end()),
        }

    return list(found.values())
