"""Technical indicator engine."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

import pandas as pd
import pandas_ta as ta


@dataclass
class IndicatorBundle:
    frame: pd.DataFrame
    snapshot: Dict[str, float]


class IndicatorEngine:
    def compute(self, price_frame: pd.DataFrame) -> IndicatorBundle:
        df = price_frame.copy()
        df["ema_21"] = ta.ema(df["close"], length=21)
        df["ema_55"] = ta.ema(df["close"], length=55)
        df["sma_50"] = ta.sma(df["close"], length=50)
        df["sma_200"] = ta.sma(df["close"], length=200)
        df["rsi_14"] = ta.rsi(df["close"], length=14)
        macd = ta.macd(df["close"], fast=12, slow=26, signal=9)
        df = pd.concat([df, macd], axis=1)
        bb = ta.bbands(df["close"], length=20, std=2)
        df = pd.concat([df, bb], axis=1)
        df["vol_sma_20"] = ta.sma(df["volume"], length=20)
        df["volatility_20"] = df["close"].pct_change().rolling(20).std() * (20 ** 0.5)
        clean = df.dropna()
        if clean.empty:
            clean = df.ffill().dropna()
        if clean.empty:
            raise ValueError("Indicator frame has no valid rows")
        latest = clean.iloc[-1]
        snapshot = {
            "price": float(latest["close"]),
            "ema_trend": float(latest["ema_21"] - latest["ema_55"]),
            "sma_trend": float(latest["sma_50"] - latest["sma_200"]),
            "rsi": float(latest["rsi_14"]),
            "macd": float(latest.get("MACD_12_26_9", 0.0)),
            "macd_signal": float(latest.get("MACDs_12_26_9", 0.0)),
            "bb_position": self._bollinger_position(latest),
            "volume_ratio": float(latest["volume"] / latest["vol_sma_20"]),
            "volatility": float(latest["volatility_20"]),
        }
        return IndicatorBundle(frame=df, snapshot=snapshot)

    def _bollinger_position(self, latest: pd.Series) -> float:
        upper = latest.get("BBU_20_2.0")
        lower = latest.get("BBL_20_2.0")
        close = latest.get("close")
        if upper is None or lower is None or close is None:
            return 0.0
        width = upper - lower
        if width == 0:
            return 0.0
        return float((close - lower) / width)
