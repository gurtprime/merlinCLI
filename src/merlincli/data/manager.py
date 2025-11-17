"""Data management utilities."""

from __future__ import annotations

import pandas as pd


class DataManager:
    def __init__(self, timeframe: str) -> None:
        self.timeframe = timeframe

    def prepare_ohlcv(self, df: pd.DataFrame) -> pd.DataFrame:
        clean = df.copy()
        clean = clean.dropna()
        if clean.empty:
            return clean
        clean = clean.sort_values("timestamp")
        clean = clean.set_index("timestamp")
        clean = clean[~clean.index.duplicated(keep="last")]
        
        # Only resample if we have enough data points and it won't cause significant data loss
        # For very short timeframes (1m, 3m, 5m), resampling can cause too much data loss
        original_count = len(clean)
        should_resample = original_count > 100 and self.timeframe not in ["1m", "3m", "5m"]
        
        if should_resample:
            try:
                resampled = clean.asfreq(self._freq_from_timeframe())
                # Only use resampled data if we don't lose more than 20% of rows
                if len(resampled.dropna()) >= original_count * 0.8:
                    clean = resampled.ffill()
                else:
                    # Resampling caused too much data loss, keep original
                    clean = clean.sort_index()
            except Exception:
                # If resampling fails, just use the data as-is
                clean = clean.sort_index()
        else:
            # For short timeframes or small datasets, don't resample - just ensure consistent index
            clean = clean.sort_index()
        
        return clean

    def _freq_from_timeframe(self) -> str:
        mapping = {
            "1m": "1min",
            "3m": "3min",
            "5m": "5min",
            "15m": "15min",
            "30m": "30min",
            "1h": "1h",
            "4h": "4h",
            "1d": "1D",
        }
        # If timeframe not in mapping, try to parse it (e.g., "3m" -> "3min")
        if self.timeframe not in mapping:
            if self.timeframe.endswith("m"):
                try:
                    minutes = int(self.timeframe[:-1])
                    return f"{minutes}min"
                except ValueError:
                    pass
            elif self.timeframe.endswith("h"):
                try:
                    hours = int(self.timeframe[:-1])
                    return f"{hours}h"
                except ValueError:
                    pass
        return mapping.get(self.timeframe, "1h")
