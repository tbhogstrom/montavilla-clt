"""Polite HTTP session: User-Agent, per-domain throttle, one retry on 5xx."""
from __future__ import annotations

import time
from typing import Callable
from urllib.parse import urlparse

import requests

from pipeline.config import USER_AGENT, HTTP_TIMEOUT, PER_DOMAIN_DELAY


class ThrottledSession:
    """A requests-backed session that throttles per-domain and retries 5xx once.

    ``get`` raises ``requests.ConnectionError`` if both the initial attempt and
    the one retry fail with a network error; 5xx responses are returned as-is
    after one retry.
    """

    def __init__(
        self,
        per_domain_delay: float = PER_DOMAIN_DELAY,
        timeout: float = HTTP_TIMEOUT,
        retry_backoff: float = 5.0,
        sleep: Callable[[float], None] = time.sleep,
        clock: Callable[[], float] = time.monotonic,
    ):
        self._per_domain_delay = per_domain_delay
        self._timeout = timeout
        self._retry_backoff = retry_backoff
        self._sleep = sleep
        self._clock = clock
        self._last_hit: dict[str, float] = {}
        self._session = requests.Session()
        self._session.headers["User-Agent"] = USER_AGENT

    def _throttle(self, host: str) -> None:
        last = self._last_hit.get(host)
        now = self._clock()
        if last is not None:
            elapsed = now - last
            if elapsed < self._per_domain_delay:
                self._sleep(self._per_domain_delay - elapsed)
        self._last_hit[host] = self._clock()

    def get(self, url: str) -> requests.Response:
        host = urlparse(url).netloc.lower()
        self._throttle(host)
        try:
            resp = self._session.get(url, timeout=self._timeout, allow_redirects=True)
        except requests.ConnectionError:
            self._sleep(self._retry_backoff)
            resp = self._session.get(url, timeout=self._timeout, allow_redirects=True)
            return resp
        if resp.status_code >= 500:
            self._sleep(self._retry_backoff)
            resp = self._session.get(url, timeout=self._timeout, allow_redirects=True)
        return resp
