"""Configuration dataclasses for merlincli."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence


@dataclass(slots=True)
class MarketConfig:
    exchange: str = "binance"
    symbol: str = "BTC/USDT"
    timeframe: str = "15m"
    limit: int = 500


@dataclass(slots=True)
class SentimentSource:
    name: str
    endpoint: str | None = None
    api_key_env: str | None = None


@dataclass(slots=True)
class SentimentConfig:
    sources: Sequence[SentimentSource] = field(
        default_factory=lambda: [SentimentSource(name="cryptopanic")]
    )
    window_hours: int = 24


@dataclass(slots=True)
class LLMConfig:
    provider: str = "gemini"
    model: str = "gemini-2.5-pro"
    api_key_env: str = "GEMINI_API_KEY"
    max_tokens: int = 15000
    temperature: float = 0.3


@dataclass(slots=True)
class StorageConfig:
    cache_dir: Path = Path("~/.cache/merlincli").expanduser()
    sqlite_path: Path = cache_dir / "merlin_cache.sqlite3"


@dataclass(slots=True)
class PipelineConfig:
    market: MarketConfig = field(default_factory=MarketConfig)
    sentiment: SentimentConfig = field(default_factory=SentimentConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)
    storage: StorageConfig = field(default_factory=StorageConfig)

    def with_env_overrides(self) -> "PipelineConfig":
        """Populate config with environment overrides when present."""
        config = PipelineConfig()
        config.market.exchange = os.getenv("MERLIN_EXCHANGE", config.market.exchange)
        config.market.symbol = os.getenv("MERLIN_SYMBOL", config.market.symbol)
        config.market.timeframe = os.getenv("MERLIN_TIMEFRAME", config.market.timeframe)
        config.llm.provider = os.getenv("MERLIN_LLM_PROVIDER", config.llm.provider)
        config.llm.model = os.getenv("MERLIN_LLM_MODEL", config.llm.model)
        config.llm.api_key_env = os.getenv("MERLIN_LLM_KEY_ENV", config.llm.api_key_env)
        if config.llm.provider.lower() == "gemini" and config.llm.api_key_env == "OPENAI_API_KEY":
            config.llm.api_key_env = "GEMINI_API_KEY"
        cache_dir = os.getenv("MERLIN_CACHE_DIR")
        if cache_dir:
            config.storage.cache_dir = Path(cache_dir).expanduser()
            config.storage.sqlite_path = config.storage.cache_dir / "merlin_cache.sqlite3"
        return config


DEFAULT_CONFIG = PipelineConfig().with_env_overrides()
