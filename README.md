# MerlinCLI – BTC/USD Market Trend Suite

MerlinCLI is a modular research stack that fetches BTC/USD market data, computes technical indicators, scores news & social sentiment, and produces human-readable trade insights with an LLM. It exposes both a CLI workflow and a Streamlit dashboard so analysts can inspect charts, metrics, and recommendations.

## Features
- **Market Data Client** – pulls OHLCV candles with `ccxt` (Binance by default) and caches recent responses in SQLite.
- **Indicator Engine** – computes EMA, SMA, RSI, MACD, Bollinger Bands, and volume/volatility diagnostics with `pandas-ta`.
- **News & Social Client** – optional sentiment data ingestion via configurable HTTP sources (disabled by default; can be configured in `config.py`).
- **Sentiment Engine** – aggregates VADER scores into buzz, bias, and compound readings.
- **Analysis Engine** – blends technical + sentiment signals into an interpretable regime and deterministic recommendation.
- **LLM Insights** – crafts structured prompts for OpenAI or Gemini (with heuristic fallback) and parses JSON guidance.
- **Outputs** – command-line summary plus a Streamlit dashboard for candle charts, indicators, and text panels.

## Project Layout
```
src/merlincli/
├── analysis/engine.py        # combines signals and emits regime
├── data/                     # market + news clients and dataframe utilities
├── dashboard/app.py          # Streamlit UI
├── indicators/engine.py      # pandas-ta metrics
├── insights/llm_client.py    # OpenAI/Gemini wiring + fallback
├── outputs/cli.py            # Click-based CLI entrypoint
├── pipeline.py               # orchestration layer
└── storage/cache.py          # SQLite cache
```

## Getting Started

### Setup Virtual Environment (Recommended)

1. Create and activate a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies (Python 3.10+):
   ```bash
   pip install --upgrade pip setuptools wheel
   pip install -e .
   ```

3. Provide API keys (optional but recommended):
   ```bash
   export OPENAI_API_KEY=\"sk-...\"       # OpenAI LLM insights
   export GEMINI_API_KEY=\"...\"          # Google Gemini LLM insights
   ```
4. Run the CLI (make sure venv is activated):
   ```bash
   python -m merlincli analyze --timeframe 1h --limit 500
   ```
   or output raw JSON:
   ```bash
   python -m merlincli dump > snapshot.json
   ```

5. Launch the dashboard:
   ```bash
   streamlit run src/merlincli/dashboard/app.py
   ```

**Note:** Always activate the virtual environment before running commands:
```bash
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

## Configuration

**📖 See [CONFIG.md](CONFIG.md) for detailed configuration guide.**

### Quick Configuration

**Main config file:** `src/merlincli/config.py`

**LLM Settings (lines 34-40):**
- `provider`: `"openai"` or `"gemini"`
- `model`: Model name (e.g., `"gpt-4o-mini"`, `"gemini-1.5-pro"`)
- `max_tokens`: Output token limit (default: 600)
- `temperature`: Creativity level 0.0-1.0 (default: 0.2)

**Environment Variables:**
```bash
export MERLIN_LLM_PROVIDER="gemini"
export MERLIN_LLM_MODEL="gemini-1.5-pro"
export GEMINI_API_KEY="your-key-here"
export MERLIN_SYMBOL="ETH/USDT"
export MERLIN_TIMEFRAME="4h"
```

- Change defaults via env vars (`MERLIN_EXCHANGE`, `MERLIN_SYMBOL`, `MERLIN_TIMEFRAME`, `MERLIN_CACHE_DIR`, `MERLIN_LLM_MODEL`, etc.).
- Switch LLM providers with `MERLIN_LLM_PROVIDER=openai|gemini` and optionally point to a custom secret using `MERLIN_LLM_KEY_ENV`.
- Extend `SentimentSource` entries in `config.py` to plug additional APIs.
- Add more indicators or rules in `indicators/engine.py` and `analysis/engine.py`.

## Notes
- Network calls gracefully degrade to synthetic data if APIs are unreachable so the pipeline still runs.
- The tool only issues research insights; it **never** places trades.

## Roadmap
- Plug additional assets (ETH/USD, SPY) by swapping `MarketConfig`.
- Add backtesting + trade journaling modules.
- Integrate websocket live updates for the dashboard.
