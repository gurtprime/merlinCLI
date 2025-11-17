"""Analysis engine combining technicals and sentiment."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

from ..config import MarketConfig
from ..indicators.engine import IndicatorBundle
from ..sentiment.engine import SentimentResult


@dataclass
class SignalBundle:
    meta: dict
    technicals: dict
    sentiment: dict
    regime: dict


class AnalysisEngine:
    def __init__(self, config: MarketConfig) -> None:
        self.config = config

    def build_signals(
        self,
        indicator_bundle: IndicatorBundle,
        sentiment_result: SentimentResult,
    ) -> SignalBundle:
        tech = indicator_bundle.snapshot
        sentiment = sentiment_result.aggregate
        frame = indicator_bundle.frame.dropna(how="any")
        latest_ts = frame.index[-1].isoformat() if not frame.empty else ""
        meta = {
            "symbol": self.config.symbol,
            "exchange": self.config.exchange,
            "timeframe": self.config.timeframe,
            "latest_timestamp": latest_ts,
            "price": tech["price"],
        }
        regime = self._compute_regime(tech, sentiment)
        return SignalBundle(meta=meta, technicals=tech, sentiment=sentiment, regime=regime)

    def _compute_regime(self, tech: Dict[str, float], sentiment: Dict[str, float]) -> dict:
        trend_score = self._normalize(tech.get("ema_trend", 0.0) + tech.get("sma_trend", 0.0))
        momentum = (tech.get("rsi", 50.0) - 50.0) / 50.0
        macd_bias = tech.get("macd", 0.0) - tech.get("macd_signal", 0.0)
        vol_pressure = tech.get("volume_ratio", 1.0) - 1.0
        sent = sentiment.get("compound", 0.0)
        composite = 0.4 * trend_score + 0.2 * momentum + 0.2 * sent + 0.1 * macd_bias + 0.1 * vol_pressure
        recommendation = "NEUTRAL"
        if composite > 0.2:
            recommendation = "LONG"
        elif composite < -0.2:
            recommendation = "SHORT"
        return {
            "composite_score": float(round(composite, 3)),
            "trend_score": float(round(trend_score, 3)),
            "momentum": float(round(momentum, 3)),
            "sentiment": float(round(sent, 3)),
            "volume_pressure": float(round(vol_pressure, 3)),
            "macd_bias": float(round(macd_bias, 3)),
            "recommendation": recommendation,
        }

    def _normalize(self, value: float) -> float:
        max_abs = 1000.0
        return max(-1.0, min(1.0, value / max_abs))
