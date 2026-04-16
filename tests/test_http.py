"""Tests for pipeline.http.ThrottledSession."""
import requests
import responses

from pipeline.http import ThrottledSession, USER_AGENT


@responses.activate
def test_get_sets_user_agent_and_returns_response():
    responses.add(responses.GET, "https://example.org/", body="hello", status=200)
    session = ThrottledSession()
    resp = session.get("https://example.org/")
    assert resp.status_code == 200
    assert resp.text == "hello"
    assert responses.calls[0].request.headers["User-Agent"] == USER_AGENT


@responses.activate
def test_get_throttles_repeated_requests_to_same_host():
    responses.add(responses.GET, "https://example.org/a", body="a", status=200)
    responses.add(responses.GET, "https://example.org/b", body="b", status=200)
    sleeps: list[float] = []
    session = ThrottledSession(per_domain_delay=0.5, sleep=sleeps.append)
    session.get("https://example.org/a")
    session.get("https://example.org/b")
    # First call has no sleep; second must sleep ~0.5s minus elapsed.
    assert len(sleeps) == 1
    assert 0 < sleeps[0] <= 0.5


@responses.activate
def test_get_does_not_throttle_across_different_hosts():
    responses.add(responses.GET, "https://a.org/", body="a", status=200)
    responses.add(responses.GET, "https://b.org/", body="b", status=200)
    sleeps: list[float] = []
    session = ThrottledSession(per_domain_delay=0.5, sleep=sleeps.append)
    session.get("https://a.org/")
    session.get("https://b.org/")
    assert sleeps == []  # different hosts, no throttle


@responses.activate
def test_get_retries_once_on_5xx():
    responses.add(responses.GET, "https://example.org/", status=503)
    responses.add(responses.GET, "https://example.org/", body="ok", status=200)
    session = ThrottledSession(retry_backoff=0, sleep=lambda s: None)
    resp = session.get("https://example.org/")
    assert resp.status_code == 200
    assert len(responses.calls) == 2


@responses.activate
def test_get_does_not_retry_on_4xx():
    responses.add(responses.GET, "https://example.org/", status=404)
    session = ThrottledSession(retry_backoff=0, sleep=lambda s: None)
    resp = session.get("https://example.org/")
    assert resp.status_code == 404
    assert len(responses.calls) == 1


@responses.activate
def test_get_retries_once_on_connection_error():
    responses.add(responses.GET, "https://example.org/", body=requests.ConnectionError())
    responses.add(responses.GET, "https://example.org/", body="ok", status=200)
    session = ThrottledSession(retry_backoff=0, sleep=lambda s: None)
    resp = session.get("https://example.org/")
    assert resp.status_code == 200
    assert len(responses.calls) == 2


@responses.activate
def test_get_propagates_connection_error_after_retry():
    responses.add(responses.GET, "https://example.org/", body=requests.ConnectionError())
    responses.add(responses.GET, "https://example.org/", body=requests.ConnectionError())
    session = ThrottledSession(retry_backoff=0, sleep=lambda s: None)
    try:
        session.get("https://example.org/")
    except requests.ConnectionError:
        pass
    else:
        raise AssertionError("expected ConnectionError to propagate after retry")
    assert len(responses.calls) == 2
