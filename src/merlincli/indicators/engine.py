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
        available_rows = len(df)
        
        # Minimum data requirement
        if available_rows < 20:
            raise ValueError(
                f"Insufficient data for indicator calculation. "
                f"Need at least 20 candles, got {available_rows}. "
                f"Try increasing the --limit parameter or using a longer timeframe."
            )
        
        # Adaptive indicator periods based on available data
        # Use shorter periods if we don't have enough data
        sma_long_period = min(200, max(50, available_rows - 10))
        sma_short_period = min(50, max(20, available_rows // 4))
        ema_long_period = min(55, max(21, available_rows // 2))
        ema_short_period = min(21, max(10, available_rows // 4))
        
        df["ema_21"] = ta.ema(df["close"], length=ema_short_period)
        df["ema_55"] = ta.ema(df["close"], length=ema_long_period)
        df["sma_50"] = ta.sma(df["close"], length=sma_short_period)
        df["sma_200"] = ta.sma(df["close"], length=sma_long_period)
        
        # Store actual periods used for reference
        self._sma_short_period = sma_short_period
        self._sma_long_period = sma_long_period
        self._ema_short_period = ema_short_period
        self._ema_long_period = ema_long_period
        df["rsi_14"] = ta.rsi(df["close"], length=14)
        
        # MACD requires at least 26 periods
        if available_rows >= 26:
            macd = ta.macd(df["close"], fast=12, slow=26, signal=9)
            df = pd.concat([df, macd], axis=1)
        else:
            # Use shorter MACD if not enough data
            fast = min(12, max(5, available_rows // 3))
            slow = min(26, max(10, available_rows // 2))
            signal = min(9, max(3, available_rows // 5))
            macd = ta.macd(df["close"], fast=fast, slow=slow, signal=signal)
            df = pd.concat([df, macd], axis=1)
        
        # Bollinger Bands require at least 20 periods
        bb_period = min(20, max(10, available_rows // 5))
        if available_rows >= 10:
            bb = ta.bbands(df["close"], length=bb_period, std=2)
            df = pd.concat([df, bb], axis=1)
        
        # Volume SMA
        vol_period = min(20, max(10, available_rows // 5))
        df["vol_sma_20"] = ta.sma(df["volume"], length=vol_period)
        
        # Volatility
        vol_window = min(20, max(10, available_rows // 5))
        df["volatility_20"] = df["close"].pct_change().rolling(vol_window).std() * (vol_window ** 0.5)
        
        # Clean data - use forward fill to preserve as much data as possible
        clean = df.dropna()
        if clean.empty:
            clean = df.ffill().dropna()
        if clean.empty:
            raise ValueError(f"Indicator frame has no valid rows. Available data: {available_rows} rows")
        
        latest = clean.iloc[-1]
        
        # Get MACD column names (may vary based on periods used)
        macd_col = None
        macd_signal_col = None
        for col in df.columns:
            if "MACD_" in col:
                # MACD line (not signal, not histogram)
                if "MACDs_" not in col and "MACDh_" not in col:
                    macd_col = col
                # MACD signal line
                elif "MACDs_" in col:
                    macd_signal_col = col
        
        # Calculate SMA trend (use available values, default to 0 if missing)
        sma_short_val = latest.get("sma_50", latest.get("close", 0))
        sma_long_val = latest.get("sma_200", latest.get("close", 0))
        sma_trend = float(sma_short_val - sma_long_val) if pd.notna(sma_short_val) and pd.notna(sma_long_val) else 0.0
        
        # Calculate EMA trend
        ema_short_val = latest.get("ema_21", latest.get("close", 0))
        ema_long_val = latest.get("ema_55", latest.get("close", 0))
        ema_trend = float(ema_short_val - ema_long_val) if pd.notna(ema_short_val) and pd.notna(ema_long_val) else 0.0
        
        # Volume ratio (handle division by zero)
        vol_sma_val = latest.get("vol_sma_20", 1.0)
        volume_val = latest.get("volume", 0.0)
        volume_ratio = float(volume_val / vol_sma_val) if vol_sma_val > 0 else 1.0
        
        snapshot = {
            "price": float(latest["close"]),
            "ema_trend": ema_trend,
            "sma_trend": sma_trend,
            "rsi": float(latest.get("rsi_14", 50.0)),
            "macd": float(latest.get(macd_col, 0.0)) if macd_col else 0.0,
            "macd_signal": float(latest.get(macd_signal_col, 0.0)) if macd_signal_col else 0.0,
            "bb_position": self._bollinger_position(latest),
            "volume_ratio": volume_ratio,
            "volatility": float(latest.get("volatility_20", 0.0)),
        }
        return IndicatorBundle(frame=df, snapshot=snapshot)

    def _bollinger_position(self, latest: pd.Series) -> float:
        # Find Bollinger Band columns (may have different periods)
        upper = None
        lower = None
        for col in latest.index:
            if "BBU_" in col:
                upper = latest.get(col)
            elif "BBL_" in col:
                lower = latest.get(col)
        
        close = latest.get("close")
        if upper is None or lower is None or close is None:
            return 0.0
        if pd.isna(upper) or pd.isna(lower) or pd.isna(close):
            return 0.0
        width = float(upper) - float(lower)
        if width == 0:
            return 0.0
        return float((float(close) - float(lower)) / width)
