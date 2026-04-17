"""Discover a CLT's website using SerpAPI + a domain plausibility heuristic."""
from __future__ import annotations

import re
from urllib.parse import urlparse

from pipeline.serpapi import SerpApiClient

BLOCKED_SUFFIXES = frozenset({
    "facebook.com",
    "linkedin.com",
    "twitter.com",
    "x.com",
    "instagram.com",
    "youtube.com",
    "yelp.com",
    "nytimes.com",
    "opb.org",
    "wikipedia.org",
    "guidestar.org",
    "candid.org",
    "charitynavigator.org",
    "propublica.org",
})

STOP_TOKENS = {
    "the", "of", "and", "for", "a", "an", "land", "trust", "community",
    "clt", "cdc", "inc", "incorporated", "association", "fund", "co",
}

_TOKEN = re.compile(r"[a-z0-9]+")


def _name_tokens(name: str) -> set[str]:
    return {t for t in _TOKEN.findall(name.lower()) if len(t) > 3 and t not in STOP_TOKENS}


def is_plausible_clt_domain(url: str, name: str) -> bool:
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    if not host:
        return False
    bare = host[4:] if host.startswith("www.") else host
    # Match blocked host exactly or as a subdomain (dot boundary); never as a bare suffix.
    if any(bare == s or bare.endswith("." + s) for s in BLOCKED_SUFFIXES):
        return False
    tokens = _name_tokens(name)
    if not tokens:
        return False
    return any(t in bare.replace("-", "").replace(".", "") for t in tokens)


def pick_best_url(organic_results: list[dict], name: str) -> str | None:
    for r in organic_results:
        link = r.get("link")
        if not link:
            continue
        if is_plausible_clt_domain(link, name):
            return link
    return None


def discover_url(client: SerpApiClient, *, name: str, city: str | None, state: str | None) -> str | None:
    """Run the canonical discovery query and return a plausible CLT URL or None."""
    parts = [f'"{name}"']
    if city:
        parts.append(f'"{city}"')
    if state:
        parts.append(state)
    parts.append("community land trust")
    query = " ".join(parts)
    data = client.search(query)
    return pick_best_url(data.get("organic_results", []), name)
