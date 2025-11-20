"""Analysis engine combining technicals and sentiment."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

import pandas as pd

from ..config import MarketConfig
from ..indicators.engine import IndicatorBundle
from ..sentiment.engine import SentimentResult


@dataclass
class SignalBundle:
    meta: dict
    technicals: dict
    sentiment: dict
    regime: dict
    price_history: dict  # Summary of recent price action


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
        price_history = self._extract_price_history(frame)
        return SignalBundle(
            meta=meta,
            technicals=tech,
            sentiment=sentiment,
            regime=regime,
            price_history=price_history,
        )

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

    def _extract_price_history(self, frame: pd.DataFrame) -> dict:
        """Extract a summary of recent price history for LLM context."""
        if frame.empty or "close" not in frame.columns:
            return {
                "candles_analyzed": 0,
                "recent_summary": "No price data available",
            }

        # Get recent candles (last 50 for context, but summarize)
        recent = frame.tail(50)
        close_prices = recent["close"].dropna()
        
        if close_prices.empty:
            return {
                "candles_analyzed": len(frame),
                "recent_summary": "Insufficient price data",
            }

        # Calculate key statistics
        current_price = float(close_prices.iloc[-1])
        period_high = float(close_prices.max())
        period_low = float(close_prices.min())
        period_open = float(close_prices.iloc[0])
        
        # Price change over the period
        price_change = current_price - period_open
        price_change_pct = (price_change / period_open * 100) if period_open > 0 else 0.0
        
        # Recent trend (last 10 vs previous 10)
        if len(close_prices) >= 20:
            recent_10_avg = float(close_prices.tail(10).mean())
            prev_10_avg = float(close_prices.iloc[-20:-10].mean())
            short_term_trend = "up" if recent_10_avg > prev_10_avg else "down"
        else:
            short_term_trend = "neutral"
        
        # Volatility (price range as % of average)
        avg_price = float(close_prices.mean())
        price_range_pct = ((period_high - period_low) / avg_price * 100) if avg_price > 0 else 0.0
        
        # Volume context if available
        volume_info = {}
        if "volume" in recent.columns:
            volumes = recent["volume"].dropna()
            if not volumes.empty:
                volume_info = {
                    "recent_avg_volume": float(volumes.tail(10).mean()),
                    "period_avg_volume": float(volumes.mean()),
                    "volume_trend": "increasing" if len(volumes) >= 10 and float(volumes.tail(5).mean()) > float(volumes.iloc[-10:-5].mean()) else "decreasing",
                }

        return {
            "candles_analyzed": len(frame),
            "recent_period_candles": len(recent),
            "current_price": current_price,
            "period_high": period_high,
            "period_low": period_low,
            "period_open": period_open,
            "price_change": round(price_change, 2),
            "price_change_pct": round(price_change_pct, 2),
            "short_term_trend": short_term_trend,
            "price_range_pct": round(price_range_pct, 2),
            **volume_info,
        }
