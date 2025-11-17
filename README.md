# 🔮 MerlinCLI – BTC/USD Market Trend Analysis Suite

A powerful, modular research tool that fetches BTC/USD market data, computes technical indicators, analyzes sentiment, and generates AI-powered trade insights. Features both a beautiful CLI interface and a Streamlit dashboard for comprehensive market analysis.

---

## ✨ Features

### 📊 Market Data & Analysis
- **Market Data Client** – Fetches OHLCV candlestick data using `ccxt` (Binance by default)
- **Intelligent Caching** – SQLite-based caching for efficient data retrieval
- **Multi-Timeframe Support** – Analyze 1m, 3m, 5m, 15m, 30m, 1h, 4h, 1d timeframes

### 📈 Technical Indicators
- **Comprehensive Indicators** – EMA, SMA, RSI, MACD, Bollinger Bands
- **Volume & Volatility Metrics** – Volume ratios and volatility calculations
- **Adaptive Calculations** – Automatically adjusts indicator periods based on available data

### 💭 Sentiment Analysis
- **News & Social Integration** – Optional sentiment data ingestion (configurable)
- **VADER Sentiment Scoring** – Aggregates sentiment into compound, positive, negative, and neutral scores
- **Flexible Sources** – Easily extendable with custom sentiment sources

### 🤖 AI-Powered Insights
- **LLM Integration** – Supports OpenAI and Google Gemini
- **Structured Recommendations** – LONG/SHORT/NEUTRAL with detailed rationale
- **Risk Assessment** – Identifies key risks and important price levels
- **Visual Price Charts** – Terminal-based charts showing support/resistance levels

### 🎨 Beautiful Output
- **Rich Terminal UI** – Color-coded tables, panels, and visualizations
- **Streamlit Dashboard** – Interactive web interface with charts and metrics
- **JSON Export** – Raw data export for integrations

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10 or higher
- Virtual environment (recommended)

### Installation

1. **Clone and navigate to the project:**
   ```bash
   cd merlinCLI
   ```

2. **Create and activate virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install --upgrade pip setuptools wheel
   pip install -e .
   ```

4. **Set up API keys (optional but recommended for LLM insights):**
   ```bash
   export GEMINI_API_KEY="your-gemini-key"      # For Gemini LLM
   export OPENAI_API_KEY="sk-..."              # For OpenAI LLM
   ```

### Usage

**Run analysis with CLI:**
```bash
python -m merlincli analyze --timeframe 15m --limit 500
```

**Export raw JSON data:**
```bash
python -m merlincli dump > snapshot.json
```

**Launch interactive dashboard:**
```bash
streamlit run src/merlincli/dashboard/app.py
```

---

## ⚙️ Configuration

📖 **For detailed configuration options, see [CONFIG.md](CONFIG.md)**

### Quick Configuration

**Main configuration file:** `src/merlincli/config.py`

#### LLM Settings
Configure in `config.py` or via environment variables:

```python
# In config.py (lines 34-40)
provider: str = "gemini"              # "openai" or "gemini"
model: str = "gemini-2.5-pro"         # Model name
max_tokens: int = 15000               # Output token limit
temperature: float = 0.3              # Creativity (0.0-1.0)
```

#### Environment Variables
```bash
# LLM Configuration
export MERLIN_LLM_PROVIDER="gemini"
export MERLIN_LLM_MODEL="gemini-2.5-pro"
export GEMINI_API_KEY="your-key-here"

# Market Configuration
export MERLIN_SYMBOL="BTC/USDT"       # Trading pair
export MERLIN_EXCHANGE="binance"      # Exchange name
export MERLIN_TIMEFRAME="15m"         # Timeframe
export MERLIN_CACHE_DIR="~/.merlin"   # Cache directory
```

#### Available Options
- **Timeframes:** `1m`, `3m`, `5m`, `15m`, `30m`, `1h`, `4h`, `1d`
- **Exchanges:** Any exchange supported by `ccxt` (Binance, Coinbase, Kraken, etc.)
- **Symbols:** Any trading pair (BTC/USDT, ETH/USDT, etc.)
- **LLM Providers:** OpenAI, Google Gemini

---

## 📋 Example Output

The CLI provides a comprehensive analysis with:

- 📊 **Market Overview** – Symbol, exchange, timeframe, current price
- 📈 **Technical Indicators** – Color-coded indicator values
- 💭 **Sentiment Analysis** – Compound, positive, negative scores
- 🎯 **Trading Regime** – Composite score and recommendation
- 🤖 **LLM Insights** – AI-generated rationale, risks, and key levels
- 📊 **Price Chart** – Visual representation of support/resistance levels

---

## 🔧 Advanced Usage

### Custom Sentiment Sources
Add custom sentiment sources in `config.py`:

```python
from merlincli.config import SentimentSource

sources = [
    SentimentSource(name="custom_api", url="https://api.example.com/news")
]
```

### Extending Indicators
Add custom indicators in `src/merlincli/indicators/engine.py`

### Custom Analysis Rules
Modify trading regime logic in `src/merlincli/analysis/engine.py`

---

## ⚠️ Important Notes

- **Research Tool Only** – This tool provides analysis and insights; it **never** executes trades
- **Graceful Degradation** – Network calls fall back to cached or synthetic data if APIs are unavailable
- **Data Caching** – All market data is cached locally for offline analysis
- **Virtual Environment** – Always activate your virtual environment before running commands

---

## 🗺️ Roadmap

- [ ] Support for additional assets (ETH/USD, SPY, etc.)
- [ ] Backtesting and trade journaling modules
- [ ] WebSocket live updates for dashboard
- [ ] Additional technical indicators
- [ ] Portfolio analysis features

---

## 📝 License

This project is provided as-is for research and educational purposes.

---

## 🤝 Contributing

Contributions are welcome! Feel free to open issues or submit pull requests.

---

**Happy Trading! 📈**
