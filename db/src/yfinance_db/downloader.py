"""Orchestrator: fetch data via client, parse, and store in SQLite."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from typing import Callable

from .client import YFinanceClient
from .db import (
    upsert_company, upsert_dividends, upsert_financials,
    upsert_prices, upsert_splits, upsert_stats,
)
from .parser import (
    parse_company, parse_dividends, parse_financials,
    parse_prices, parse_splits, parse_stats,
)


def download_company(
    conn: sqlite3.Connection,
    client: YFinanceClient,
    ticker: str,
    force: bool = False,
    period: str = "5y",
) -> dict[str, int]:
    """Download all data for a single company. Returns counts per data type."""
    ticker = ticker.upper()
    now_str = datetime.now(timezone.utc).isoformat()
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # Check if recently downloaded (within 24h) unless forced
    if not force:
        cur = conn.execute(
            "SELECT last_downloaded FROM companies WHERE ticker = ?", (ticker,)
        )
        row = cur.fetchone()
        if row and row[0]:
            last = datetime.fromisoformat(row[0])
            age = datetime.now(timezone.utc) - last
            if age.total_seconds() < 86400:
                return {}  # Already fresh

    counts: dict[str, int] = {}

    # Company info + stats
    info = client.get_info(ticker)
    company = parse_company(ticker, info, now_str)
    upsert_company(conn, company)

    stat = parse_stats(ticker, info, today_str)
    upsert_stats(conn, stat)
    counts["stats"] = 1

    # Price history
    price_df = client.get_history(ticker, period=period)
    price_rows = parse_prices(ticker, price_df)
    counts["prices"] = upsert_prices(conn, price_rows)

    # Financial statements
    for stmt_name, fetch_method in [
        ("income", client.get_income_statement),
        ("balance", client.get_balance_sheet),
        ("cashflow", client.get_cashflow),
    ]:
        for quarterly in [False, True]:
            period_type = "quarterly" if quarterly else "annual"
            try:
                df = fetch_method(ticker, quarterly=quarterly)
                fin_rows = parse_financials(ticker, df, stmt_name, period_type)
                count = upsert_financials(conn, fin_rows)
                key = f"{stmt_name}_{period_type}"
                counts[key] = count
            except Exception:
                pass  # Some companies may not have all statements

    # Dividends
    try:
        div_series = client.get_dividends(ticker)
        div_rows = parse_dividends(ticker, div_series)
        counts["dividends"] = upsert_dividends(conn, div_rows)
    except Exception:
        counts["dividends"] = 0

    # Splits
    try:
        split_series = client.get_splits(ticker)
        split_rows = parse_splits(ticker, split_series)
        counts["splits"] = upsert_splits(conn, split_rows)
    except Exception:
        counts["splits"] = 0

    return counts


def download_batch(
    conn: sqlite3.Connection,
    client: YFinanceClient,
    tickers: list[str],
    force: bool = False,
    period: str = "5y",
    progress_callback: Callable[[str, int, int], None] | None = None,
) -> dict[str, dict[str, int]]:
    """Download data for multiple tickers. Returns {ticker: counts}."""
    results: dict[str, dict[str, int]] = {}
    total = len(tickers)
    for i, ticker in enumerate(tickers, 1):
        if progress_callback:
            progress_callback(ticker, i, total)
        try:
            counts = download_company(conn, client, ticker, force=force, period=period)
            results[ticker] = counts
        except Exception as exc:
            results[ticker] = {"error": -1}
            if progress_callback:
                progress_callback(f"ERROR: {ticker}: {exc}", i, total)
    return results
