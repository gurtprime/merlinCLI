"""Streamlit dashboard for BTC/USD analysis."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from ..config import PipelineConfig
from ..pipeline import MerlinPipeline

st.set_page_config(page_title="Merlin BTC/USD Dashboard", layout="wide")


def run_pipeline(timeframe: str, limit: int):
    @st.cache_data(show_spinner=True)
    def _run(tf: str, lim: int):
        config = PipelineConfig()
        config.market.timeframe = tf
        config.market.limit = lim
        pipeline = MerlinPipeline(config=config)
        return pipeline.run()

    return _run(timeframe, limit)


def render_chart(indicator_frame: pd.DataFrame):
    fig = go.Figure()
    fig.add_trace(
        go.Candlestick(
            x=indicator_frame["timestamp"],
            open=indicator_frame["open"],
            high=indicator_frame["high"],
            low=indicator_frame["low"],
            close=indicator_frame["close"],
            name="Price",
        )
    )
    for col in ["ema_21", "ema_55", "sma_50", "sma_200", "BBU_20_2.0", "BBL_20_2.0"]:
        if col in indicator_frame:
            fig.add_trace(go.Scatter(x=indicator_frame["timestamp"], y=indicator_frame[col], name=col))
    fig.update_layout(height=600, margin=dict(l=10, r=10, t=30, b=30))
    st.plotly_chart(fig, use_container_width=True)


def main():
    st.title("Merlin BTC/USD Market Trend Dashboard")
    timeframe = st.sidebar.selectbox("Timeframe", ["1h", "4h", "1d"], index=0)
    limit = st.sidebar.slider("Candles", min_value=200, max_value=1000, value=500, step=100)
    result = run_pipeline(timeframe, limit)
    st.subheader("Snapshot")
    cols = st.columns(4)
    cols[0].metric("Price", f"{result['meta']['price']:.2f}")
    cols[1].metric("Recommendation", result["regime"]["recommendation"])
    cols[2].metric("Composite Score", result["regime"]["composite_score"])
    cols[3].metric("Sentiment", result["sentiment"]["compound"])
    indicator_frame = pd.DataFrame(result["indicator_frame"])
    render_chart(indicator_frame)
    st.subheader("Sentiment")
    st.write(result["sentiment"])
    st.subheader("LLM Insight")
    st.write(result["llm"]["rationale"])
    st.write("Risks: ", result["llm"].get("risks"))
    st.write("Key levels:", result["llm"].get("key_levels"))
    st.subheader("Raw Data Preview")
    st.dataframe(indicator_frame.tail(100))


if __name__ == "__main__":
    main()
