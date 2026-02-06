"""Orchestrator: resolve CIK, fetch company facts, parse, and store."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from typing import Any, Callable

from .client import EdgarClient
from .config import Config
from .db import connect_db, resolve_cik, upsert_company, upsert_facts, upsert_ticker_map
from .models import Company
from .parser import parse_company_facts


def _build_ticker_map(client: EdgarClient) -> dict[str, int]:
    """Fetch SEC company_tickers.json and return {TICKER: cik}."""
    data = client.get_company_tickers()
    mapping: dict[str, int] = {}
    for entry in data.values():
        ticker = entry.get("ticker", "").upper()
        cik = entry.get("cik_str")
        if ticker and cik:
            mapping[ticker] = int(cik)
    return mapping


def refresh_ticker_map(
    conn: sqlite3.Connection, client: EdgarClient
) -> dict[str, int]:
    """Download and cache ticker→CIK map."""
    mapping = _build_ticker_map(client)
    upsert_ticker_map(conn, mapping)
    return mapping


def download_company(
    conn: sqlite3.Connection,
    client: EdgarClient,
    ticker: str,
    force: bool = False,
) -> int:
    """Download and store data for a single company. Returns number of facts stored."""
    ticker = ticker.upper()

    # Resolve CIK
    cik = resolve_cik(conn, ticker)
    if cik is None:
        # Try refreshing the ticker map
        refresh_ticker_map(conn, client)
        cik = resolve_cik(conn, ticker)
        if cik is None:
            raise ValueError(f"Unknown ticker: {ticker}")

    # Check if recently downloaded (within 24h) unless forced
    if not force:
        cur = conn.execute(
            "SELECT last_downloaded FROM companies WHERE cik = ?", (cik,)
        )
        row = cur.fetchone()
        if row and row[0]:
            last = datetime.fromisoformat(row[0])
            age = datetime.now(timezone.utc) - last
            if age.total_seconds() < 86400:
                return 0  # Already fresh

    # Fetch company facts
    data = client.get_company_facts(cik)

    # Store company info
    entity = data.get("entityName", ticker)
    company = Company(
        cik=cik,
        name=entity,
        ticker=ticker,
        last_downloaded=datetime.now(timezone.utc).isoformat(),
    )
    upsert_company(conn, company)

    # Parse and store facts
    facts = parse_company_facts(cik, data)
    count = upsert_facts(conn, facts)
    return count


def download_batch(
    conn: sqlite3.Connection,
    client: EdgarClient,
    tickers: list[str],
    force: bool = False,
    progress_callback: Callable[[str, int, int], None] | None = None,
) -> dict[str, int]:
    """Download data for multiple tickers. Returns {ticker: fact_count}."""
    # Ensure ticker map is loaded
    refresh_ticker_map(conn, client)

    results: dict[str, int] = {}
    total = len(tickers)
    for i, ticker in enumerate(tickers, 1):
        if progress_callback:
            progress_callback(ticker, i, total)
        try:
            count = download_company(conn, client, ticker, force=force)
            results[ticker] = count
        except Exception as exc:
            results[ticker] = -1  # Signal error
            if progress_callback:
                progress_callback(f"ERROR: {ticker}: {exc}", i, total)
    return results
