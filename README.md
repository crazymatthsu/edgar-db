# edgar-db

Download SEC EDGAR financial data and Yahoo Finance market data into local SQLite databases. Query from Python, the command line, or through a web UI.

**Data sources**:
- [SEC EDGAR](https://www.sec.gov/edgar) REST APIs (free, no API key, 10 req/sec rate limit)
- [Yahoo Finance](https://finance.yahoo.com/) via the `yfinance` library (prices, financials, dividends, splits, stats)

## Packages

| Package | Description | Docs |
|---|---|---|
| **edgar_db** | Core library — download, store, and query SEC XBRL financial data | [db/README.md](db/README.md) |
| **yfinance_db** | Yahoo Finance — download prices, financials, dividends, splits, and stats | — |
| **edgar_ui** | Web UI — FastAPI REST backend + Streamlit frontend | [ui/README.md](ui/README.md) |

## Quick Start

```bash
# Install everything
pip install -e ".[all]"

# --- SEC EDGAR ---

# Set required SEC user agent
export EDGAR_USER_AGENT="YourAppName your@email.com"

# Download SEC data
edgar-db download -t AAPL -t MSFT -t GOOGL
edgar-db download --sp500                      # all S&P 500

# View from the command line
edgar-db show AAPL
edgar-db info

# --- Yahoo Finance ---

# Download market data
yfinance-db download -t AAPL -t MSFT -t GOOGL
yfinance-db download --sp500                   # all S&P 500

# View from the command line
yfinance-db show AAPL
yfinance-db show AAPL --data prices
yfinance-db info

# --- Web UI ---

# Start the API server
uvicorn edgar_ui.backend.app:app --host 0.0.0.0 --port 8000

# Start the web UI
streamlit run ui/src/edgar_ui/frontend/app.py
```

## Configuration

| Variable | Required | Default | Description |
|---|---|---|---|
| `EDGAR_USER_AGENT` | Yes (edgar_db) | — | SEC requires a user agent string (e.g. `"MyApp me@email.com"`) |
| `EDGAR_DB_PATH` | No | `~/.edgar-db/edgar.db` | Custom path for the SEC EDGAR SQLite database |
| `YFINANCE_DB_PATH` | No | `~/.yfinance-db/yfinance.db` | Custom path for the Yahoo Finance SQLite database |

## Requirements

- Python 3.10+

## Development

```bash
pip install -e ".[all,dev]"
pytest db/tests/ ui/tests/
```

### Test summary

| Suite | Tests | Description |
|---|---|---|
| `db/tests/` | 41 | Core edgar_db (client, parser, db, query, cli) |
| `db/tests/test_yfinance/` | 47 | yfinance_db (client, parser, db, query, cli) |
| `ui/tests/` | 38 | UI backend routes and frontend components |
| **Total** | **126** | |
