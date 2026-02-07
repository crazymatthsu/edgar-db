"""Parse yfinance data structures into model dataclasses."""

from __future__ import annotations

from datetime import date
from typing import Any

import pandas as pd

from .models import (
    CompanyRow, CompanyStatRow, DividendRow, FinancialRow, PriceRow, SplitRow,
)

# Mapping from yfinance info keys to CompanyStatRow fields
_STAT_KEY_MAP = {
    "marketCap": "market_cap",
    "trailingPE": "pe_ratio",
    "forwardPE": "forward_pe",
    "pegRatio": "peg_ratio",
    "priceToBook": "price_to_book",
    "enterpriseValue": "enterprise_value",
    "enterpriseToEbitda": "ev_to_ebitda",
    "profitMargins": "profit_margin",
    "operatingMargins": "operating_margin",
    "returnOnEquity": "roe",
    "returnOnAssets": "roa",
    "revenueGrowth": "revenue_growth",
    "earningsGrowth": "earnings_growth",
    "dividendYield": "dividend_yield",
    "beta": "beta",
    "fiftyTwoWeekHigh": "fifty_two_week_high",
    "fiftyTwoWeekLow": "fifty_two_week_low",
    "averageVolume": "avg_volume",
    "sharesOutstanding": "shares_outstanding",
    "floatShares": "float_shares",
    "shortRatio": "short_ratio",
}


def parse_company(ticker: str, info: dict[str, Any], downloaded: str) -> CompanyRow:
    return CompanyRow(
        ticker=ticker.upper(),
        name=info.get("longName") or info.get("shortName", ticker),
        sector=info.get("sector", ""),
        industry=info.get("industry", ""),
        market_cap=float(info.get("marketCap", 0) or 0),
        last_downloaded=downloaded,
    )


def parse_stats(ticker: str, info: dict[str, Any], fetched: str) -> CompanyStatRow:
    kwargs: dict[str, Any] = {"ticker": ticker.upper(), "fetched_date": fetched}
    for yf_key, field_name in _STAT_KEY_MAP.items():
        val = info.get(yf_key)
        if val is not None:
            kwargs[field_name] = float(val) if isinstance(val, (int, float)) else 0.0
    return CompanyStatRow(**kwargs)


def parse_prices(
    ticker: str, df: pd.DataFrame, interval: str = "1d"
) -> list[PriceRow]:
    rows: list[PriceRow] = []
    ticker = ticker.upper()
    for idx, row in df.iterrows():
        dt = idx.strftime("%Y-%m-%d") if hasattr(idx, "strftime") else str(idx)[:10]
        rows.append(PriceRow(
            ticker=ticker,
            date=dt,
            interval=interval,
            open=float(row.get("Open", 0)),
            high=float(row.get("High", 0)),
            low=float(row.get("Low", 0)),
            close=float(row.get("Close", 0)),
            volume=int(row.get("Volume", 0)),
        ))
    return rows


def parse_financials(
    ticker: str,
    df: pd.DataFrame,
    statement: str,
    period_type: str,
) -> list[FinancialRow]:
    """Parse a yfinance financial statement DataFrame into FinancialRows.

    yfinance returns DataFrames with metrics as rows and dates as columns.
    """
    rows: list[FinancialRow] = []
    ticker = ticker.upper()
    if df.empty:
        return rows

    for col in df.columns:
        period_end = col.strftime("%Y-%m-%d") if hasattr(col, "strftime") else str(col)[:10]
        for metric_name in df.index:
            val = df.at[metric_name, col]
            if pd.isna(val):
                continue
            rows.append(FinancialRow(
                ticker=ticker,
                statement=statement,
                period_type=period_type,
                period_end=period_end,
                metric=str(metric_name),
                value=float(val),
            ))
    return rows


def parse_dividends(ticker: str, series: pd.Series) -> list[DividendRow]:
    rows: list[DividendRow] = []
    ticker = ticker.upper()
    for idx, val in series.items():
        dt = idx.strftime("%Y-%m-%d") if hasattr(idx, "strftime") else str(idx)[:10]
        rows.append(DividendRow(ticker=ticker, date=dt, amount=float(val)))
    return rows


def parse_splits(ticker: str, series: pd.Series) -> list[SplitRow]:
    rows: list[SplitRow] = []
    ticker = ticker.upper()
    for idx, val in series.items():
        dt = idx.strftime("%Y-%m-%d") if hasattr(idx, "strftime") else str(idx)[:10]
        rows.append(SplitRow(ticker=ticker, date=dt, ratio=float(val)))
    return rows
