"""Tests for pipeline.discover."""
from pipeline.discover import is_plausible_clt_domain, pick_best_url


def test_is_plausible_rejects_social_platforms():
    name = "Proud Ground"
    assert not is_plausible_clt_domain("https://facebook.com/proudground", name)
    assert not is_plausible_clt_domain("https://www.linkedin.com/company/proudground", name)
    assert not is_plausible_clt_domain("https://twitter.com/proudground", name)
    assert not is_plausible_clt_domain("https://x.com/proudground", name)
    assert not is_plausible_clt_domain("https://instagram.com/proudground", name)
    assert not is_plausible_clt_domain("https://www.youtube.com/c/proudground", name)


def test_is_plausible_rejects_news_and_directory_sites():
    assert not is_plausible_clt_domain("https://nytimes.com/article", "Proud Ground")
    assert not is_plausible_clt_domain("https://opb.org/news", "Proud Ground")
    assert not is_plausible_clt_domain("https://yelp.com/biz/proudground", "Proud Ground")


def test_is_plausible_requires_name_token_in_domain():
    assert not is_plausible_clt_domain("https://landtrust.org/", "The Land Trust")
    assert is_plausible_clt_domain("https://proudground.org/", "Proud Ground")
    assert is_plausible_clt_domain("https://www.sabincdc.org/", "Sabin CDC")


def test_pick_best_url_returns_first_plausible():
    organic = [
        {"link": "https://facebook.com/proudground"},
        {"link": "https://proudground.org/"},
        {"link": "https://example.com/"},
    ]
    assert pick_best_url(organic, name="Proud Ground") == "https://proudground.org/"


def test_pick_best_url_returns_none_when_no_match():
    organic = [{"link": "https://facebook.com/x"}, {"link": "https://yelp.com/x"}]
    assert pick_best_url(organic, name="Whatever CLT") is None


def test_pick_best_url_handles_missing_link_field():
    organic = [{}, {"link": "https://proudground.org/"}]
    assert pick_best_url(organic, name="Proud Ground") == "https://proudground.org/"


def test_is_plausible_rejects_subdomain_of_blocked_but_accepts_same_suffix_sld():
    # Subdomains of blocked hosts must still be blocked.
    assert not is_plausible_clt_domain("https://pages.facebook.com/proudground", "Proud Ground")
    # A SLD that happens to end with a blocked host's string (no dot boundary)
    # is NOT a subdomain and must NOT be blocked.
    assert is_plausible_clt_domain("https://proudgroundfacebook.com/", "Proud Ground")


def test_discover_url_composes_query_and_returns_plausible_match():
    from pipeline.discover import discover_url
    from pipeline.serpapi import SerpApiClient, normalized_query_hash

    class StubCache:
        def __init__(self):
            self.queries: list[str] = []
            self.payload = {"organic_results": [
                {"link": "https://facebook.com/proudground"},
                {"link": "https://proudground.org/"},
            ]}
        def get(self, h):
            return None
        def put(self, h, query, response):
            self.queries.append(query)

    cache = StubCache()

    class StubClient(SerpApiClient):
        def search(self, query, *, location=None):
            cache.put(normalized_query_hash(query), query, cache.payload)
            return cache.payload

    client = StubClient(api_key="x", cache=cache)
    result = discover_url(client, name="Proud Ground", city="Portland", state="OR")
    assert result == "https://proudground.org/"
    assert cache.queries == ['"Proud Ground" "Portland" OR community land trust']


def test_discover_url_returns_none_when_no_plausible_result():
    from pipeline.discover import discover_url
    from pipeline.serpapi import SerpApiClient

    class NoopCache:
        def get(self, h): return None
        def put(self, h, query, response): pass

    class NoMatchClient(SerpApiClient):
        def search(self, query, *, location=None):
            return {"organic_results": [{"link": "https://facebook.com/x"}]}

    client = NoMatchClient(api_key="x", cache=NoopCache())
    assert discover_url(client, name="Whatever CLT", city=None, state=None) is None
