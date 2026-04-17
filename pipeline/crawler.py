"""Crawl a CLT's homepage + contact-like pages, store HTML on disk."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path

import requests

from pipeline.http import ThrottledSession
from pipeline.links import find_contact_links
from pipeline.robots import RobotsCache


@dataclass
class FetchedPage:
    url: str
    page_kind: str  # 'home' | 'about' | 'contact' | 'staff' | 'team' | 'board'
    http_status: int | None
    html_path: str | None
    content_hash: str | None
    error: str | None


@dataclass
class CrawlResult:
    clt_id: str
    pages: list[FetchedPage] = field(default_factory=list)

    @property
    def success(self) -> bool:
        return any(p.html_path is not None for p in self.pages)


def _content_path(html_dir: Path, clt_id: str, page_kind: str, body: bytes) -> Path:
    h = hashlib.sha256(body).hexdigest()[:8]
    out = html_dir / clt_id
    out.mkdir(parents=True, exist_ok=True)
    return out / f"{page_kind}-{h}.html"


def _fetch(session: ThrottledSession, robots: RobotsCache, url: str, page_kind: str,
           html_dir: Path, clt_id: str) -> FetchedPage:
    if not robots.allowed(url):
        return FetchedPage(url=url, page_kind=page_kind, http_status=None,
                           html_path=None, content_hash=None, error="robots-disallowed")
    try:
        resp = session.get(url)
    except requests.RequestException as exc:
        return FetchedPage(url=url, page_kind=page_kind, http_status=None,
                           html_path=None, content_hash=None, error=str(exc))
    if resp.status_code != 200:
        return FetchedPage(url=url, page_kind=page_kind, http_status=resp.status_code,
                           html_path=None, content_hash=None,
                           error=f"http-{resp.status_code}")
    body = resp.content
    path = _content_path(html_dir, clt_id, page_kind, body)
    try:
        path.write_bytes(body)
    except OSError as exc:
        return FetchedPage(url=url, page_kind=page_kind, http_status=200,
                           html_path=None, content_hash=None,
                           error=f"io-error: {exc}")
    return FetchedPage(url=url, page_kind=page_kind, http_status=200,
                       html_path=str(path), content_hash=hashlib.sha256(body).hexdigest(),
                       error=None)


def crawl_one(clt_id: str, url: str, session: ThrottledSession,
              robots: RobotsCache, html_dir: Path) -> CrawlResult:
    """Crawl one CLT: homepage + contact-like links. Returns CrawlResult with all pages."""
    result = CrawlResult(clt_id=clt_id)
    home = _fetch(session, robots, url, "home", Path(html_dir), clt_id)
    result.pages.append(home)
    if home.html_path is None:
        return result
    html = Path(home.html_path).read_text(encoding="utf-8", errors="replace")
    for link_url, kind in find_contact_links(html, base_url=url):
        page = _fetch(session, robots, link_url, kind, Path(html_dir), clt_id)
        result.pages.append(page)
    return result
