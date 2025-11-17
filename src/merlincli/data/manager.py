"""Data management utilities."""

from __future__ import annotations

import pandas as pd


class DataManager:
    def __init__(self, timeframe: str) -> None:
        self.timeframe = timeframe

    def prepare_ohlcv(self, df: pd.DataFrame) -> pd.DataFrame:
        clean = df.copy()
        clean = clean.dropna()
        clean = clean.sort_values("timestamp")
        clean = clean.set_index("timestamp")
        clean = clean[~clean.index.duplicated(keep="last")]
        clean = clean.asfreq(self._freq_from_timeframe())
        clean = clean.ffill()
        return clean

    def _freq_from_timeframe(self) -> str:
        mapping = {
            "1m": "1min",
            "5m": "5min",
            "15m": "15min",
            "1h": "1h",
            "4h": "4h",
            "1d": "1D",
        }
        return mapping.get(self.timeframe, "1h")
