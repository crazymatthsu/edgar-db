"""Shared helpers for fetching index component lists from Wikipedia."""

from __future__ import annotations

from io import StringIO
from typing import Callable

import httpx
import pandas as pd

_HEADERS = {"User-Agent": "edgar-db/0.1 (https://github.com; financial data tool)"}


def _fetch_wikipedia_tickers(url: str, ticker_columns: list[str]) -> list[str]:
    """Fetch tickers from a Wikipedia page table.

    Searches all tables on the page for a column matching one of *ticker_columns*.
    Returns cleaned ticker list (dots replaced with dashes for SEC compatibility).
    """
    resp = httpx.get(url, headers=_HEADERS, follow_redirects=True)
    resp.raise_for_status()
    tables = pd.read_html(StringIO(resp.text))

    for df in tables:
        for col in ticker_columns:
            if col in df.columns:
                tickers = df[col].dropna().str.strip().tolist()
                return [t.replace(".", "-") for t in tickers]

    raise ValueError(f"Could not find ticker column in any table (tried {ticker_columns})")


# ---------------------------------------------------------------------------
# Per-index fetchers
# ---------------------------------------------------------------------------

_SPX_URL = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
_DJI_URL = "https://en.wikipedia.org/wiki/Dow_Jones_Industrial_Average"
_NDX_URL = "https://en.wikipedia.org/wiki/Nasdaq-100"


def get_spx_tickers() -> list[str]:
    """Fetch current S&P 500 component tickers from Wikipedia."""
    return _fetch_wikipedia_tickers(_SPX_URL, ["Symbol", "Ticker symbol", "Ticker"])


def get_dji_tickers() -> list[str]:
    """Fetch current Dow Jones Industrial Average component tickers from Wikipedia."""
    return _fetch_wikipedia_tickers(_DJI_URL, ["Symbol", "Ticker", "Ticker symbol"])


def get_ndx_tickers() -> list[str]:
    """Fetch current Nasdaq-100 component tickers from Wikipedia."""
    return _fetch_wikipedia_tickers(_NDX_URL, ["Ticker", "Symbol", "Ticker symbol"])


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

INDEXES: dict[str, tuple[str, Callable[[], list[str]]]] = {
    "SPX": ("S&P 500", get_spx_tickers),
    "DJI": ("Dow Jones Industrial Average", get_dji_tickers),
    "NDX": ("Nasdaq-100", get_ndx_tickers),
}


def get_index_tickers(index_code: str) -> list[str]:
    """Return component tickers for the given index code."""
    code = index_code.upper()
    if code not in INDEXES:
        raise ValueError(f"Unknown index: {code}. Supported: {list(INDEXES)}")
    _, fetcher = INDEXES[code]
    return fetcher()


def list_supported_indexes() -> list[str]:
    """Return sorted list of supported index codes."""
    return sorted(INDEXES)
