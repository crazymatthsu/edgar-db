from __future__ import annotations

import pandas as pd

from yfinance_db.parser import (
    parse_company, parse_dividends, parse_financials,
    parse_prices, parse_splits, parse_stats,
)


def test_parse_company() -> None:
    info = {
        "longName": "Apple Inc.",
        "sector": "Technology",
        "industry": "Consumer Electronics",
        "marketCap": 3_000_000_000_000,
    }
    company = parse_company("aapl", info, "2024-01-01T00:00:00")
    assert company.ticker == "AAPL"
    assert company.name == "Apple Inc."
    assert company.sector == "Technology"
    assert company.market_cap == 3_000_000_000_000.0


def test_parse_company_short_name_fallback() -> None:
    info = {"shortName": "AAPL", "marketCap": 1000}
    company = parse_company("aapl", info, "2024-01-01")
    assert company.name == "AAPL"


def test_parse_stats() -> None:
    info = {
        "trailingPE": 30.5,
        "forwardPE": 28.0,
        "beta": 1.2,
        "dividendYield": 0.005,
        "marketCap": 3_000_000_000_000,
    }
    stat = parse_stats("aapl", info, "2024-01-01")
    assert stat.ticker == "AAPL"
    assert stat.pe_ratio == 30.5
    assert stat.beta == 1.2
    assert stat.dividend_yield == 0.005


def test_parse_prices() -> None:
    dates = pd.to_datetime(["2024-01-02", "2024-01-03"])
    df = pd.DataFrame(
        {
            "Open": [185.0, 186.0],
            "High": [186.0, 187.0],
            "Low": [184.0, 185.0],
            "Close": [185.5, 186.5],
            "Volume": [50_000_000, 45_000_000],
        },
        index=dates,
    )
    rows = parse_prices("aapl", df)
    assert len(rows) == 2
    assert rows[0].ticker == "AAPL"
    assert rows[0].date == "2024-01-02"
    assert rows[0].close == 185.5
    assert rows[1].volume == 45_000_000


def test_parse_financials() -> None:
    dates = pd.to_datetime(["2023-09-30", "2022-09-30"])
    df = pd.DataFrame(
        {dates[0]: [383_285e6, 97_000e6], dates[1]: [394_328e6, 99_803e6]},
        index=["Total Revenue", "Net Income"],
    )
    rows = parse_financials("aapl", df, "income", "annual")
    assert len(rows) == 4
    assert all(r.ticker == "AAPL" for r in rows)
    assert all(r.statement == "income" for r in rows)

    revenues = [r for r in rows if r.metric == "Total Revenue"]
    assert len(revenues) == 2


def test_parse_financials_empty() -> None:
    df = pd.DataFrame()
    rows = parse_financials("aapl", df, "income", "annual")
    assert rows == []


def test_parse_financials_skips_nan() -> None:
    dates = pd.to_datetime(["2023-09-30"])
    df = pd.DataFrame(
        {dates[0]: [100.0, float("nan")]},
        index=["Revenue", "Missing"],
    )
    rows = parse_financials("aapl", df, "income", "annual")
    assert len(rows) == 1
    assert rows[0].metric == "Revenue"


def test_parse_dividends() -> None:
    series = pd.Series(
        [0.24, 0.24],
        index=pd.to_datetime(["2024-01-15", "2024-04-15"]),
    )
    rows = parse_dividends("aapl", series)
    assert len(rows) == 2
    assert rows[0].amount == 0.24


def test_parse_splits() -> None:
    series = pd.Series(
        [4.0, 7.0],
        index=pd.to_datetime(["2020-08-31", "2014-06-09"]),
    )
    rows = parse_splits("aapl", series)
    assert len(rows) == 2
    assert rows[0].ratio == 4.0
