"""Tests for pipeline.serpapi.SerpApiClient."""
import responses

from pipeline.serpapi import SerpApiClient, normalized_query_hash, ENDPOINT


class FakeCache:
    def __init__(self):
        self.store: dict[str, dict] = {}

    def get(self, query_hash: str):
        return self.store.get(query_hash)

    def put(self, query_hash: str, query: str, response: dict):
        self.store[query_hash] = response


def test_normalized_query_hash_is_stable():
    h1 = normalized_query_hash("  Hello  WORLD  ")
    h2 = normalized_query_hash("hello world")
    assert h1 == h2
    assert len(h1) == 64


@responses.activate
def test_search_caches_response_on_first_call():
    payload = {"organic_results": [{"link": "https://example.org/"}]}
    responses.add(responses.GET, ENDPOINT, json=payload, status=200)
    cache = FakeCache()
    client = SerpApiClient(api_key="KEY", cache=cache)

    result = client.search("community land trust portland or")
    assert result == payload
    assert len(cache.store) == 1
    assert len(responses.calls) == 1


@responses.activate
def test_search_returns_cached_without_http():
    cache = FakeCache()
    cache.put(normalized_query_hash("foo"), "foo", {"cached": True})
    client = SerpApiClient(api_key="KEY", cache=cache)
    result = client.search("foo")
    assert result == {"cached": True}
    assert len(responses.calls) == 0


@responses.activate
def test_search_raises_on_non_200():
    responses.add(responses.GET, ENDPOINT, status=500, body="boom")
    cache = FakeCache()
    client = SerpApiClient(api_key="KEY", cache=cache)
    try:
        client.search("anything")
    except RuntimeError as exc:
        assert "500" in str(exc)
    else:
        raise AssertionError("expected RuntimeError")


@responses.activate
def test_search_passes_query_and_api_key():
    payload = {"organic_results": []}
    responses.add(responses.GET, ENDPOINT, json=payload, status=200)
    cache = FakeCache()
    client = SerpApiClient(api_key="MYKEY", cache=cache)
    client.search("something")
    sent = responses.calls[0].request.url
    assert "q=something" in sent
    assert "api_key=MYKEY" in sent
    assert "engine=google" in sent


@responses.activate
def test_search_with_location_sends_location_and_uses_distinct_cache_key():
    payload = {"organic_results": []}
    responses.add(responses.GET, ENDPOINT, json=payload, status=200)
    cache = FakeCache()
    client = SerpApiClient(api_key="KEY", cache=cache)
    client.search("foo", location="Portland, OR")
    sent = responses.calls[0].request.url
    assert "location=Portland" in sent
    # cache key composed with |loc= suffix must differ from the no-location key
    assert normalized_query_hash("foo") not in cache.store
    assert normalized_query_hash("foo|loc=Portland, OR") in cache.store
