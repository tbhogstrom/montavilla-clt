"""SerpAPI client with a pluggable cache backend.

The cache interface is two methods: get(hash) -> response or None; and
put(hash, query, response). Production cache backed by inv_serpapi_cache
in Postgres; tests use an in-memory dict.
"""
from __future__ import annotations

import hashlib
import json
from typing import Protocol

import requests

from pipeline.config import HTTP_TIMEOUT, USER_AGENT
from pipeline.db import connect

ENDPOINT = "https://serpapi.com/search.json"


class Cache(Protocol):
    def get(self, query_hash: str) -> dict | None: ...
    def put(self, query_hash: str, query: str, response: dict) -> None: ...


def normalized_query_hash(query: str) -> str:
    norm = " ".join(query.lower().split())
    return hashlib.sha256(norm.encode("utf-8")).hexdigest()


class SerpApiClient:
    def __init__(self, api_key: str, cache: Cache):
        self._api_key = api_key
        self._cache = cache

    def search(self, query: str, *, location: str | None = None) -> dict:
        h = normalized_query_hash(query if location is None else f"{query}|loc={location}")
        cached = self._cache.get(h)
        if cached is not None:
            return cached
        params = {
            "engine": "google",
            "q": query,
            "api_key": self._api_key,
            "num": 10,
        }
        if location is not None:
            params["location"] = location
        resp = requests.get(
            ENDPOINT,
            params=params,
            headers={"User-Agent": USER_AGENT},
            timeout=HTTP_TIMEOUT,
        )
        if resp.status_code != 200:
            raise RuntimeError(f"SerpAPI returned {resp.status_code}: {resp.text[:200]}")
        data = resp.json()
        self._cache.put(h, query, data)
        return data


class PostgresCache:
    """Cache backed by inv_serpapi_cache (used in production runs)."""

    def get(self, query_hash: str) -> dict | None:
        with connect() as conn, conn.cursor() as cur:
            cur.execute(
                "SELECT response_json FROM inv_serpapi_cache WHERE query_hash = %s",
                (query_hash,),
            )
            row = cur.fetchone()
            return row[0] if row else None

    def put(self, query_hash: str, query: str, response: dict) -> None:
        with connect() as conn, conn.cursor() as cur:
            cur.execute(
                "INSERT INTO inv_serpapi_cache (query_hash, query, response_json) "
                "VALUES (%s, %s, %s::jsonb) ON CONFLICT (query_hash) DO NOTHING",
                (query_hash, query, json.dumps(response)),
            )
            conn.commit()
