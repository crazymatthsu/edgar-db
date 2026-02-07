# CLAUDE.md — edgar-db

## Project Overview
Download SEC EDGAR XBRL financial data into SQLite for AI and quantitative analysis.
Two packages: `edgar_db` (core library) and `edgar_ui` (FastAPI + Streamlit UI).

## Project Structure
- `db/src/edgar_db/` — Core library (query, db, downloader, client, parser, config, models, xbrl_tags)
- `db/tests/` — Core tests
- `ui/src/edgar_ui/backend/` — FastAPI REST API
- `ui/src/edgar_ui/frontend/` — Streamlit + Plotly UI
- `ui/tests/` — UI tests

## Development Commands
- Install dev: `pip install -e ".[dev,all]"`
- Run all tests: `pytest db/tests/ ui/tests/`
- Run core tests: `pytest db/tests/`
- Run UI tests: `pytest ui/tests/`
- CLI entry point: `edgar-db` (defined in `edgar_db.cli:cli`)

## Code Conventions
- Import as `edgar_db` and `edgar_ui`, never `db` or `ui`
- All DB access goes through `EdgarQuery(conn)`, never raw SQL in routes
- `STATEMENT_COLUMNS` in `xbrl_tags.py` is the source of truth for financial metric names
- Use `_make_fact(**overrides)` factory pattern in tests
- Dependency direction: `ui → db` only. Never import from `ui` in `db`.

## Gotchas
- SQLite threading: Use `check_same_thread=False` in test fixtures (FastAPI TestClient uses a separate thread)
- FastAPI route ordering: Static paths (e.g. `/{ticker}/compare`) must be registered BEFORE dynamic paths (e.g. `/{ticker}/{metric}`)
- `get_config()` requires `EDGAR_USER_AGENT` env var — mock `get_config` in download tests
- Plotly area charts: `px.area()` uses `stackgroup`, not `fill`
