"""Tests for pipeline.extractor."""
from pathlib import Path

from pipeline.extractor import extract_emails, normalize_email

FIXTURE = Path(__file__).parent / "fixtures" / "sample_contact.html"


def test_normalize_email_lowercases_and_strips():
    assert normalize_email("  Info@SampleCLT.org. ") == "info@sampleclt.org"


def test_extract_emails_picks_up_mailto():
    html = FIXTURE.read_text()
    found = extract_emails(html)
    sources = {(e["email"], e["source"]) for e in found}
    assert ("info@sampleclt.org", "mailto") in sources


def test_extract_emails_picks_up_visible_text():
    html = FIXTURE.read_text()
    found = extract_emails(html)
    assert any(e["email"] == "director@sampleclt.org" and e["source"] == "text" for e in found)


def test_extract_emails_deobfuscates_at_and_dot_patterns():
    html = FIXTURE.read_text()
    emails = {e["email"] for e in extract_emails(html) if e["source"] == "deobfuscated"}
    assert "programs@sampleclt.org" in emails
    assert "outreach@sampleclt.org" in emails
    assert "volunteer@sampleclt.org" in emails


def test_extract_emails_filters_junk_domains():
    html = FIXTURE.read_text()
    emails = {e["email"] for e in extract_emails(html)}
    assert "noreply@example.com" not in emails
    assert "form@wixpress.com" not in emails
    assert "noreply@sentry.io" not in emails


def test_extract_emails_filters_image_filename_false_positive():
    html = FIXTURE.read_text()
    emails = {e["email"] for e in extract_emails(html)}
    assert not any(e.endswith(".png") for e in emails)


def test_extract_emails_includes_context_snippet():
    html = FIXTURE.read_text()
    found = extract_emails(html)
    director = next(e for e in found if e["email"] == "director@sampleclt.org")
    assert "Director" in director["context"]
    assert len(director["context"]) <= 200
