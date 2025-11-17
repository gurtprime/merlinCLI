"""News and social sentiment data ingestion."""

from __future__ import annotations

import logging
from typing import Iterable, List

import requests
from tenacity import retry, stop_after_attempt, wait_fixed

from ..config import SentimentConfig, SentimentSource
from ..storage.cache import CacheManager

logger = logging.getLogger(__name__)


class NewsSocialClient:
    def __init__(self, config: SentimentConfig, cache: CacheManager | None = None) -> None:
        self.config = config
        self.cache = cache

    def fetch_texts(self, limit: int = 100, use_cache: bool = True) -> List[dict]:
        cache_key = f"sentiment::{limit}::{self.config.window_hours}"
        if use_cache and self.cache:
            cached = self.cache.get(cache_key)
            if cached:
                logger.info("Loaded %s sentiment documents from cache", len(cached))
                return cached
        docs: List[dict] = []
        for source in self.config.sources:
            docs.extend(self._safe_fetch_source(source, limit=limit))
        if self.cache:
            self.cache.set(cache_key, docs, ttl_seconds=900)
        return docs

    def _safe_fetch_source(self, source: SentimentSource, limit: int) -> List[dict]:
        try:
            return list(self._fetch_source(source, limit))
        except Exception as exc:  # pragma: no cover - network
            logger.error("Failed fetching from %s: %s", source.name, exc)
            return self._synthetic_news(source.name)

    @retry(stop=stop_after_attempt(2), wait=wait_fixed(2))
    def _fetch_source(self, source: SentimentSource, limit: int) -> Iterable[dict]:
        if source.name.lower() == "cryptopanic":
            token = self._resolve_api_key(source)
            url = source.endpoint or "https://cryptopanic.com/api/v1/posts/"
            params = {"currencies": "BTC", "public": "true", "limit": min(50, limit)}
            if token:
                params["auth_token"] = token
            resp = requests.get(url, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            for post in data.get("results", [])[:limit]:
                yield {
                    "source": source.name,
                    "text": post.get("title") or "",
                    "published_at": post.get("published_at"),
                    "domain": post.get("domain"),
                }
            return
        if not source.endpoint:
            raise ValueError(f"Source {source.name} missing endpoint")
        headers = {}
        token = self._resolve_api_key(source)
        if token:
            headers["Authorization"] = f"Bearer {token}"
        resp = requests.get(source.endpoint, headers=headers, timeout=10)
        resp.raise_for_status()
        payload = resp.json()
        articles = payload.get("articles") or payload.get("data") or []
        for entry in articles[:limit]:
            text = entry.get("title") or entry.get("content") or ""
            yield {
                "source": source.name,
                "text": text,
                "published_at": entry.get("publishedAt") or entry.get("published_at"),
                "url": entry.get("url"),
            }

    def _resolve_api_key(self, source: SentimentSource) -> str | None:
        if source.api_key_env:
            from os import getenv

            return getenv(source.api_key_env)
        return None

    def _synthetic_news(self, source_name: str) -> List[dict]:
        logger.warning("Using synthetic sentiment docs for %s", source_name)
        return [
            {
                "source": source_name,
                "text": "Bitcoin steady as market awaits macro cues.",
                "published_at": None,
            },
            {
                "source": source_name,
                "text": "On-chain data hints at accumulation from long-term holders.",
                "published_at": None,
            },
        ]
