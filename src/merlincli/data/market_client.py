"""Market data client using ccxt."""

from __future__ import annotations

import logging
from dataclasses import asdict
from typing import Any, Dict, List

import pandas as pd
from tenacity import retry, stop_after_attempt, wait_exponential

try:
    import ccxt  # type: ignore
except ImportError as exc:  # pragma: no cover - module import guard
    raise RuntimeError(
        "ccxt must be installed to use MarketDataClient"
    ) from exc

from ..config import MarketConfig
from ..storage.cache import CacheManager

logger = logging.getLogger(__name__)


class MarketDataClient:
    def __init__(self, config: MarketConfig, cache: CacheManager | None = None) -> None:
        self.config = config
        self.cache = cache
        exchange_cls = getattr(ccxt, config.exchange)
        self.exchange = exchange_cls({"enableRateLimit": True})

    def _cache_key(self) -> str:
        return (
            f"ohlcv::{self.config.exchange}::{self.config.symbol}::"
            f"{self.config.timeframe}::{self.config.limit}"
        )

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, max=10))
    def _fetch_remote(self) -> List[List[Any]]:
        return self.exchange.fetch_ohlcv(
            symbol=self.config.symbol,
            timeframe=self.config.timeframe,
            limit=self.config.limit,
        )

    def fetch_ohlcv(self, use_cache: bool = True) -> pd.DataFrame:
        key = self._cache_key()
        if use_cache and self.cache:
            cached = self.cache.get(key)
            if cached:
                logger.info("Loaded OHLCV data from cache")
                df = pd.DataFrame(cached)
                # Convert timestamp string back to datetime
                df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
                return df
        try:
            raw = self._fetch_remote()
            df = pd.DataFrame(
                raw,
                columns=["timestamp", "open", "high", "low", "close", "volume"],
            )
            df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
        except Exception as exc:  # pragma: no cover - network fallback
            logger.error("Failed to fetch live data: %s", exc)
            df = self._synthetic_data()
        if self.cache:
            # Convert timestamp to ISO string for JSON serialization
            df_cache = df.copy()
            df_cache["timestamp"] = df_cache["timestamp"].apply(lambda x: x.isoformat() if pd.notna(x) else None)
            self.cache.set(key, df_cache.to_dict(orient="records"), ttl_seconds=300)
        return df

    def _synthetic_data(self) -> pd.DataFrame:
        import numpy as np

        logger.warning("Generating synthetic OHLCV data for fallback use")
        periods = self.config.limit
        idx = pd.date_range(end=pd.Timestamp.utcnow(), periods=periods, freq=self.config.timeframe)
        prices = 30000 + np.cumsum(np.random.randn(periods)) * 50
        high = prices + np.random.rand(periods) * 30
        low = prices - np.random.rand(periods) * 30
        open_ = prices + np.random.randn(periods)
        close = prices + np.random.randn(periods)
        volume = np.abs(np.random.randn(periods)) * 100
        return pd.DataFrame(
            {
                "timestamp": idx,
                "open": open_,
                "high": high,
                "low": low,
                "close": close,
                "volume": volume,
            }
        )
