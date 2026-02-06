# EDGAR Financial Database — Web UI

Interactive web interface for the EDGAR financial database, with a FastAPI REST backend and Streamlit frontend.

## Architecture

```
┌─────────────────┐     HTTP/JSON     ┌──────────────────┐
│  Streamlit UI   │ ◄──────────────► │  FastAPI Backend  │
│  (frontend/)    │                   │  (backend/)       │
└─────────────────┘                   └────────┬─────────┘
                                               │
                                        ┌──────┴──────┐
                                        │   SQLite    │
                                        │  edgar.db   │
                                        └─────────────┘
```

The backend and frontend can run on different machines. The backend runs on the server with the SQLite database, and the frontend connects to the backend via HTTP.

## Setup

```bash
# Install all dependencies (from project root)
pip install -e ".[all]"

# Or install only what you need:
pip install -e ".[api]"   # Backend only (FastAPI + uvicorn)
pip install -e ".[ui]"    # Frontend only (Streamlit + Plotly + httpx)
```

## Running the Backend

```bash
# Set required SEC EDGAR user agent
export EDGAR_USER_AGENT="YourApp your@email.com"

# Optional: set custom database path (default: ~/.edgar-db/edgar.db)
export EDGAR_DB_PATH="/path/to/edgar.db"

# Start the API server
uvicorn ui.backend.app:app --host 0.0.0.0 --port 8000

# API docs available at: http://localhost:8000/docs
```

## Running the Frontend

```bash
# Set the backend API URL (default: http://localhost:8000)
export EDGAR_API_URL="http://localhost:8000"

# Start Streamlit
streamlit run ui/frontend/app.py

# Opens in browser at: http://localhost:8501
```

## API Reference

### Health
- `GET /api/health` — Server health check
- `GET /api/stats` — Database statistics (companies, facts, tickers)

### Download
- `POST /api/download/{ticker}?force=false` — Download SEC data for a ticker

### Statements
- `GET /api/statements/{ticker}/income?period=annual` — Income statement
- `GET /api/statements/{ticker}/balance?period=annual` — Balance sheet
- `GET /api/statements/{ticker}/cashflow?period=annual` — Cash flow statement

### Metrics
- `GET /api/metrics/available` — List all available metrics by statement type
- `GET /api/metrics/{ticker}/{metric}?period=annual` — Single metric time series
- `GET /api/metrics/{ticker}/compare?metrics=revenue,net_income&period=annual` — Compare metrics

## Running Tests

```bash
# Install dev + all dependencies
pip install -e ".[all,dev]"

# Run all UI tests
pytest ui/tests/ -v
```

## Streamlit Cloud Deployment

1. Push your repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Select your repo, branch, and set the main file to `ui/frontend/app.py`
4. Set secrets/environment variables:
   - `EDGAR_API_URL` — URL of your running FastAPI backend
