"""Tests for pipeline.links."""
from pathlib import Path

from pipeline.links import find_contact_links, classify_page_kind

FIXTURE = Path(__file__).parent / "fixtures" / "sample_homepage.html"


def test_find_contact_links_returns_same_domain_only():
    html = FIXTURE.read_text()
    links = find_contact_links(html, base_url="https://sampleclt.org/")
    urls = [u for u, _ in links]
    assert "https://sampleclt.org/about-us" in urls
    assert "https://sampleclt.org/our-team/" in urls
    assert "https://sampleclt.org/board-of-directors" in urls
    assert "https://sampleclt.org/contact-us" in urls
    assert "https://sampleclt.org/get-involved/staff" in urls
    assert not any("facebook.com" in u for u in urls)
    assert not any("other-domain.org" in u for u in urls)
    assert not any(u.endswith("/news") for u in urls)


def test_find_contact_links_returns_classified_kinds():
    html = FIXTURE.read_text()
    links = dict(find_contact_links(html, base_url="https://sampleclt.org/"))
    assert links["https://sampleclt.org/about-us"] == "about"
    assert links["https://sampleclt.org/our-team/"] == "team"
    assert links["https://sampleclt.org/board-of-directors"] == "board"
    assert links["https://sampleclt.org/contact-us"] == "contact"
    assert links["https://sampleclt.org/get-involved/staff"] == "staff"


def test_find_contact_links_caps_at_max():
    nav = "".join(f'<a href="/contact-{i}">Contact {i}</a>' for i in range(20))
    html = f"<html><body>{nav}</body></html>"
    links = find_contact_links(html, base_url="https://x.org/")
    assert len(links) == 8


def test_find_contact_links_dedupes_by_url():
    html = '<a href="/contact">a</a><a href="/contact">b</a>'
    links = find_contact_links(f"<html><body>{html}</body></html>", base_url="https://x.org/")
    assert len(links) == 1


def test_classify_page_kind_priority():
    assert classify_page_kind("/contact-us", "Contact") == "contact"
    assert classify_page_kind("/about", "About") == "about"
    assert classify_page_kind("/our-staff", "Staff") == "staff"
    assert classify_page_kind("/team", "The Team") == "team"
    assert classify_page_kind("/board", "Board") == "board"
    assert classify_page_kind("/get-involved", "Contact") == "contact"


def test_classify_page_kind_returns_none_for_non_matching():
    assert classify_page_kind("/news", "Latest News") is None
    assert classify_page_kind("/", "Home") is None
    assert classify_page_kind("/get-involved", "") is None


def test_find_contact_links_same_host_ignores_explicit_default_port():
    html = '<a href="https://sampleclt.org/about">A</a>'
    links = find_contact_links(html, base_url="https://sampleclt.org:443/")
    assert len(links) == 1
    assert links[0][0] == "https://sampleclt.org/about"
