"""Primary orchestration pipeline for BTC/USD analysis."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, Dict

import pandas as pd

from .analysis.engine import AnalysisEngine
from .config import DEFAULT_CONFIG, PipelineConfig
from .data.manager import DataManager
from .data.market_client import MarketDataClient
from .data.news_social_client import NewsSocialClient
from .indicators.engine import IndicatorEngine
from .insights.llm_client import LLMInsightsClient
from .sentiment.engine import SentimentEngine
from .storage.cache import CacheManager


class MerlinPipeline:
    def __init__(self, config: PipelineConfig | None = None) -> None:
        self.config = config or DEFAULT_CONFIG
        self.cache = CacheManager(self.config.storage.sqlite_path)
        self.market_client = MarketDataClient(self.config.market, cache=self.cache)
        self.news_client = NewsSocialClient(self.config.sentiment, cache=self.cache)
        self.data_manager = DataManager(self.config.market.timeframe)
        self.indicator_engine = IndicatorEngine()
        self.sentiment_engine = SentimentEngine()
        self.analysis_engine = AnalysisEngine(self.config.market)
        self.llm_client = LLMInsightsClient(self.config.llm)

    def run(self) -> Dict[str, Any]:
        ohlcv = self.market_client.fetch_ohlcv()
        clean = self.data_manager.prepare_ohlcv(ohlcv)
        indicators = self.indicator_engine.compute(clean)
        docs = self.news_client.fetch_texts()
        sentiment = self.sentiment_engine.score_documents(docs)
        signals = self.analysis_engine.build_signals(indicators, sentiment)
        llm = self.llm_client.generate(
            {
                "meta": signals.meta,
                "technicals": signals.technicals,
                "sentiment": signals.sentiment,
                "regime": signals.regime,
                "price_history": signals.price_history,
            }
        )
        # Convert indicator frame to dict, handling timestamp serialization
        indicator_dict = indicators.frame.tail(200).reset_index()
        if "timestamp" in indicator_dict.columns:
            indicator_dict["timestamp"] = indicator_dict["timestamp"].apply(
                lambda x: x.isoformat() if pd.notna(x) else None
            )
        indicator_records = indicator_dict.to_dict(orient="records")
        
        # Convert sentiment frame to dict, handling timestamp serialization if present
        sentiment_dict = sentiment.frame.tail(200).copy()
        if "timestamp" in sentiment_dict.columns:
            sentiment_dict["timestamp"] = sentiment_dict["timestamp"].apply(
                lambda x: x.isoformat() if pd.notna(x) else None
            )
        sentiment_records = sentiment_dict.to_dict(orient="records")
        
        return {
            "meta": signals.meta,
            "technicals": signals.technicals,
            "sentiment": signals.sentiment,
            "regime": signals.regime,
            "llm": asdict(llm),
            "indicator_frame": indicator_records,
            "sentiment_frame": sentiment_records,
        }

    def to_dataframe(self) -> pd.DataFrame:
        result = self.run()
        return pd.DataFrame(result["indicator_frame"])
