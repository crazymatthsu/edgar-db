"""Orchestrator: fetch data via clients, parse, and store in SQLite."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from typing import Callable

from .client import OpenFIGIClient, YFinanceClient
from .db import upsert_security
from .parser import build_security_row, parse_yfinance_info


def download_security(
    conn: sqlite3.Connection,
    yf_client: YFinanceClient,
    figi_client: OpenFIGIClient | None,
    ticker: str,
    force: bool = False,
) -> bool:
    ticker = ticker.upper()
    now_str = datetime.now(timezone.utc).isoformat()

    if not force:
        cur = conn.execute(
            "SELECT last_updated FROM securities WHERE ticker = ?", (ticker,)
        )
        row = cur.fetchone()
        if row and row[0]:
            last = datetime.fromisoformat(row[0])
            age = datetime.now(timezone.utc) - last
            if age.total_seconds() < 86400:
                return False

    info = yf_client.get_info(ticker)
    yf_data = parse_yfinance_info(ticker, info)

    figi_data = None
    if figi_client is not None:
        figi_data = figi_client.fetch_figi(ticker)

    security = build_security_row(ticker, yf_data, figi_data, now_str)
    upsert_security(conn, security)
    return True


def download_batch(
    conn: sqlite3.Connection,
    yf_client: YFinanceClient,
    figi_client: OpenFIGIClient | None,
    tickers: list[str],
    force: bool = False,
    progress_callback: Callable[[str, int, int], None] | None = None,
) -> dict[str, bool | str]:
    results: dict[str, bool | str] = {}
    total = len(tickers)
    for i, ticker in enumerate(tickers, 1):
        if progress_callback:
            progress_callback(ticker, i, total)
        try:
            downloaded = download_security(
                conn, yf_client, figi_client, ticker, force=force
            )
            results[ticker] = downloaded
        except Exception as exc:
            results[ticker] = f"error: {exc}"
            if progress_callback:
                progress_callback(f"ERROR: {ticker}: {exc}", i, total)
    return results
