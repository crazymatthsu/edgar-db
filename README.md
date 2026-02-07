# edgar-db

Download SEC EDGAR financial data (income statement, balance sheet, cash flow) into a local SQLite database. Query it from Python, the command line, or through a web UI.

**Data source**: [SEC EDGAR](https://www.sec.gov/edgar) REST APIs (free, no API key, 10 req/sec rate limit)

## Packages

| Package | Description | Docs |
|---|---|---|
| **edgar_db** | Core library — download, store, and query SEC financial data | [db/README.md](db/README.md) |
| **edgar_ui** | Web UI — FastAPI REST backend + Streamlit frontend | [ui/README.md](ui/README.md) |

## Quick Start

```bash
# Install everything
pip install -e ".[all]"

# Set required SEC user agent
export EDGAR_USER_AGENT="YourAppName your@email.com"

# Download data
python3 -m edgar_db download --ticker AAPL MSFT GOOGL

# View from the command line
python3 -m edgar_db show AAPL

# Start the API server
uvicorn edgar_ui.backend.app:app --host 0.0.0.0 --port 8000

# Start the web UI
streamlit run ui/src/edgar_ui/frontend/app.py
```

## Requirements

- Python 3.10+
- `EDGAR_USER_AGENT` environment variable (required by SEC)

## Development

```bash
pip install -e ".[all,dev]"
pytest db/tests/ ui/tests/
```
