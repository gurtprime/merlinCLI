# Configuration Guide

## Main Configuration File

The main configuration file is located at:
```
src/merlincli/config.py
```

This file contains all default settings organized into dataclasses:

### LLM Configuration (`LLMConfig`)

Located at lines **34-40** in `config.py`:

```python
@dataclass(slots=True)
class LLMConfig:
    provider: str = "openai"              # "openai" or "gemini"
    model: str = "gpt-4o-mini"            # Model name
    api_key_env: str = "OPENAI_API_KEY"   # Environment variable name
    max_tokens: int = 600                  # Max output tokens
    temperature: float = 0.2               # Creativity (0.0-1.0)
```

**To modify LLM settings:**

1. **Edit directly in code** (lines 35-40):
   ```python
   class LLMConfig:
       provider: str = "gemini"           # Change to "gemini"
       model: str = "gemini-1.5-pro"      # Change model
       api_key_env: str = "GEMINI_API_KEY"
       max_tokens: int = 1000             # Increase token limit
       temperature: float = 0.3           # Adjust creativity
   ```

2. **Use environment variables** (recommended):
   ```bash
   export MERLIN_LLM_PROVIDER="gemini"
   export MERLIN_LLM_MODEL="gemini-1.5-pro"
   export MERLIN_LLM_KEY_ENV="GEMINI_API_KEY"
   ```

### Market Configuration (`MarketConfig`)

Located at lines **11-16**:

```python
@dataclass(slots=True)
class MarketConfig:
    exchange: str = "binance"      # Exchange name
    symbol: str = "BTC/USDT"       # Trading pair
    timeframe: str = "1h"          # Candlestick interval
    limit: int = 500              # Number of candles
```

**Environment variables:**
- `MERLIN_EXCHANGE` - Exchange name
- `MERLIN_SYMBOL` - Trading pair (e.g., "ETH/USDT")
- `MERLIN_TIMEFRAME` - Timeframe (e.g., "4h", "1d")

### Sentiment Configuration (`SentimentConfig`)

Located at lines **26-31**:

```python
@dataclass(slots=True)
class SentimentConfig:
    sources: Sequence[SentimentSource] = field(...)
    window_hours: int = 24  # Time window for sentiment analysis
```

### Storage Configuration (`StorageConfig`)

Located at lines **43-46**:

```python
@dataclass(slots=True)
class StorageConfig:
    cache_dir: Path = Path("~/.cache/merlincli").expanduser()
    sqlite_path: Path = cache_dir / "merlin_cache.sqlite3"
```

**Environment variable:**
- `MERLIN_CACHE_DIR` - Custom cache directory path

## Configuration Methods

### Method 1: Environment Variables (Recommended)

Create a `.env` file in the project root (or export in your shell):

```bash
# LLM Settings
export MERLIN_LLM_PROVIDER="gemini"
export MERLIN_LLM_MODEL="gemini-1.5-pro"
export MERLIN_LLM_KEY_ENV="GEMINI_API_KEY"

# Market Settings
export MERLIN_EXCHANGE="binance"
export MERLIN_SYMBOL="BTC/USDT"
export MERLIN_TIMEFRAME="4h"

# API Keys
export GEMINI_API_KEY="your-api-key-here"
export OPENAI_API_KEY="sk-your-key-here"  # If using OpenAI
# Note: News sentiment sources are disabled by default (can be added in config.py if needed)

# Storage
export MERLIN_CACHE_DIR="~/.cache/merlincli"
```

### Method 2: Direct Code Modification

Edit `src/merlincli/config.py` and change the default values in the dataclasses.

### Method 3: Programmatic Configuration

In your code, create a custom config:

```python
from merlincli.config import PipelineConfig, LLMConfig, MarketConfig

config = PipelineConfig()
config.llm.provider = "gemini"
config.llm.model = "gemini-1.5-pro"
config.llm.temperature = 0.3
config.market.symbol = "ETH/USDT"
config.market.timeframe = "4h"

pipeline = MerlinPipeline(config=config)
```

## Available LLM Models

### OpenAI Models
- `gpt-4o-mini` (default, cost-effective)
- `gpt-4o`
- `gpt-4-turbo`
- `gpt-3.5-turbo`

### Gemini Models
- `gemini-1.5-pro`
- `gemini-1.5-flash`
- `gemini-pro`

## Quick Reference

| Setting | Config File | Environment Variable | Default |
|---------|------------|---------------------|---------|
| LLM Provider | `LLMConfig.provider` | `MERLIN_LLM_PROVIDER` | `"openai"` |
| LLM Model | `LLMConfig.model` | `MERLIN_LLM_MODEL` | `"gpt-4o-mini"` |
| API Key Env | `LLMConfig.api_key_env` | `MERLIN_LLM_KEY_ENV` | `"OPENAI_API_KEY"` |
| Max Tokens | `LLMConfig.max_tokens` | - | `600` |
| Temperature | `LLMConfig.temperature` | - | `0.2` |
| Exchange | `MarketConfig.exchange` | `MERLIN_EXCHANGE` | `"binance"` |
| Symbol | `MarketConfig.symbol` | `MERLIN_SYMBOL` | `"BTC/USDT"` |
| Timeframe | `MarketConfig.timeframe` | `MERLIN_TIMEFRAME` | `"1h"` |
| Cache Dir | `StorageConfig.cache_dir` | `MERLIN_CACHE_DIR` | `~/.cache/merlincli` |

