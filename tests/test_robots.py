"""Tests for pipeline.robots.RobotsCache."""
import responses

from pipeline.robots import RobotsCache


@responses.activate
def test_allows_when_robots_missing():
    responses.add(responses.GET, "https://example.org/robots.txt", status=404)
    cache = RobotsCache()
    assert cache.allowed("https://example.org/contact")


@responses.activate
def test_disallowed_path_blocked():
    body = "User-agent: *\nDisallow: /private/\n"
    responses.add(responses.GET, "https://example.org/robots.txt", body=body, status=200)
    cache = RobotsCache()
    assert not cache.allowed("https://example.org/private/secret")
    assert cache.allowed("https://example.org/contact")


@responses.activate
def test_robots_fetched_once_per_host():
    responses.add(responses.GET, "https://example.org/robots.txt", body="", status=200)
    cache = RobotsCache()
    cache.allowed("https://example.org/a")
    cache.allowed("https://example.org/b")
    assert len(responses.calls) == 1


@responses.activate
def test_network_error_treated_as_allowed():
    responses.add(responses.GET, "https://example.org/robots.txt", body=ConnectionError("boom"))
    cache = RobotsCache()
    assert cache.allowed("https://example.org/anything")
