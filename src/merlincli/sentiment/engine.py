"""Sentiment analysis engine using VADER."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List

import pandas as pd
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer


@dataclass
class SentimentResult:
    frame: pd.DataFrame
    aggregate: dict


class SentimentEngine:
    def __init__(self) -> None:
        self.analyzer = SentimentIntensityAnalyzer()

    def score_documents(self, docs: Iterable[dict]) -> SentimentResult:
        rows: List[dict] = []
        for doc in docs:
            text = doc.get("text") or ""
            scores = self.analyzer.polarity_scores(text)
            rows.append({
                **doc,
                **scores,
            })
        frame = pd.DataFrame(rows) if rows else pd.DataFrame(columns=["compound"])
        aggregate = self._aggregate(frame)
        return SentimentResult(frame=frame, aggregate=aggregate)

    def _aggregate(self, frame: pd.DataFrame) -> dict:
        if frame.empty:
            return {"compound": 0.0, "pos": 0.0, "neg": 0.0, "neu": 0.0, "buzz": 0}
        agg = frame[["compound", "pos", "neg", "neu"]].mean().to_dict()
        agg["buzz"] = len(frame)
        agg["bias"] = float(agg["pos"] - agg["neg"])
        return agg
