"""Fetch the S&P 500 ticker list from Wikipedia."""

from __future__ import annotations

import httpx


_WIKI_URL = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"


def get_sp500_tickers() -> list[str]:
    """Fetch current S&P 500 tickers from Wikipedia.

    Parses the first table on the Wikipedia page to extract ticker symbols.
    """
    try:
        import pandas as pd
    except ImportError:
        raise ImportError("pandas is required for S&P 500 list fetching")

    # Use httpx to fetch HTML to avoid macOS SSL cert issues with urllib
    from io import StringIO

    headers = {"User-Agent": "edgar-db/0.1 (https://github.com; financial data tool)"}
    resp = httpx.get(_WIKI_URL, headers=headers, follow_redirects=True)
    resp.raise_for_status()
    tables = pd.read_html(StringIO(resp.text))
    df = tables[0]

    # The column is typically "Symbol" or "Ticker symbol"
    for col in ["Symbol", "Ticker symbol", "Ticker"]:
        if col in df.columns:
            tickers = df[col].dropna().str.strip().tolist()
            # Clean tickers: some have dots (BRK.B → BRK-B for SEC)
            return [t.replace(".", "-") for t in tickers]

    raise ValueError("Could not find ticker column in S&P 500 table")
