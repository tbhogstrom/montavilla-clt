"""Per-host robots.txt cache. Fetched once per host; failures fail open (allow)."""
from __future__ import annotations

from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import requests

from pipeline.config import USER_AGENT, HTTP_TIMEOUT


class RobotsCache:
    def __init__(self):
        self._parsers: dict[str, RobotFileParser] = {}

    def _load(self, host_url: str) -> RobotFileParser:
        rp = RobotFileParser()
        try:
            resp = requests.get(
                f"{host_url}/robots.txt",
                headers={"User-Agent": USER_AGENT},
                timeout=HTTP_TIMEOUT,
            )
            if resp.status_code == 200:
                rp.parse(resp.text.splitlines())
            else:
                rp.parse([])  # treat as fully open
        except (requests.RequestException, OSError):
            rp.parse([])
        return rp

    def allowed(self, url: str) -> bool:
        parsed = urlparse(url)
        host_url = f"{parsed.scheme}://{parsed.netloc}"
        if host_url not in self._parsers:
            self._parsers[host_url] = self._load(host_url)
        return self._parsers[host_url].can_fetch(USER_AGENT, url)
