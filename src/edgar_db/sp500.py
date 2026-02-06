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

    tables = pd.read_html(_WIKI_URL)
    df = tables[0]

    # The column is typically "Symbol" or "Ticker symbol"
    for col in ["Symbol", "Ticker symbol", "Ticker"]:
        if col in df.columns:
            tickers = df[col].dropna().str.strip().tolist()
            # Clean tickers: some have dots (BRK.B → BRK-B for SEC)
            return [t.replace(".", "-") for t in tickers]

    raise ValueError("Could not find ticker column in S&P 500 table")
