"""Tests for pipeline.crawler.crawl_one."""
from pathlib import Path

import responses

from pipeline.crawler import crawl_one, CrawlResult
from pipeline.http import ThrottledSession
from pipeline.robots import RobotsCache


HOMEPAGE = """
<html><body>
  <a href="/about">About</a>
  <a href="/contact">Contact</a>
  <a href="/staff">Staff</a>
</body></html>
"""


@responses.activate
def test_crawl_one_fetches_homepage_plus_contact_links(tmp_path):
    base = "https://sampleclt.org"
    responses.add(responses.GET, f"{base}/robots.txt", body="", status=200)
    responses.add(responses.GET, f"{base}/", body=HOMEPAGE, status=200)
    responses.add(responses.GET, f"{base}/about", body="<p>about</p>", status=200)
    responses.add(responses.GET, f"{base}/contact", body="<p>contact</p>", status=200)
    responses.add(responses.GET, f"{base}/staff", body="<p>staff</p>", status=200)

    session = ThrottledSession(per_domain_delay=0, sleep=lambda s: None)
    robots = RobotsCache()
    result = crawl_one(
        clt_id="sample-clt",
        url=f"{base}/",
        session=session,
        robots=robots,
        html_dir=tmp_path,
    )
    assert isinstance(result, CrawlResult)
    assert result.success
    kinds = sorted(p.page_kind for p in result.pages)
    assert kinds == ["about", "contact", "home", "staff"]
    assert all(Path(p.html_path).exists() for p in result.pages)
    assert all(Path(p.html_path).is_relative_to(tmp_path / "sample-clt") for p in result.pages)


@responses.activate
def test_crawl_one_records_404_as_page_with_error(tmp_path):
    base = "https://sampleclt.org"
    responses.add(responses.GET, f"{base}/robots.txt", body="", status=200)
    responses.add(responses.GET, f"{base}/", body="<a href='/contact'>c</a>", status=200)
    responses.add(responses.GET, f"{base}/contact", status=404)

    session = ThrottledSession(per_domain_delay=0, sleep=lambda s: None)
    robots = RobotsCache()
    result = crawl_one("c", f"{base}/", session, robots, tmp_path)
    contact = next(p for p in result.pages if p.page_kind == "contact")
    assert contact.http_status == 404
    assert contact.error is not None


@responses.activate
def test_crawl_one_homepage_failure_marks_overall_failure(tmp_path):
    base = "https://deadclt.org"
    responses.add(responses.GET, f"{base}/robots.txt", body="", status=200)
    responses.add(responses.GET, f"{base}/", status=500)
    responses.add(responses.GET, f"{base}/", status=500)  # retry

    session = ThrottledSession(per_domain_delay=0, sleep=lambda s: None, retry_backoff=0)
    robots = RobotsCache()
    result = crawl_one("c", f"{base}/", session, robots, tmp_path)
    assert not result.success
    assert result.pages[0].page_kind == "home"
    assert result.pages[0].http_status == 500


@responses.activate
def test_crawl_one_respects_robots_disallow(tmp_path):
    base = "https://sampleclt.org"
    responses.add(responses.GET, f"{base}/robots.txt",
                  body="User-agent: *\nDisallow: /private/", status=200)
    responses.add(responses.GET, f"{base}/", body="<a href='/private/contact'>c</a>", status=200)

    session = ThrottledSession(per_domain_delay=0, sleep=lambda s: None)
    robots = RobotsCache()
    result = crawl_one("c", f"{base}/", session, robots, tmp_path)
    private = next((p for p in result.pages if p.url.endswith("/private/contact")), None)
    assert private is not None
    assert private.error == "robots-disallowed"
    assert private.html_path is None
