from __future__ import annotations

import sqlite3

import pytest

from yfinance_db.db import (
    upsert_company, upsert_dividends, upsert_financials,
    upsert_prices, upsert_splits, upsert_stats,
)
from yfinance_db.query import YFinanceQuery

from .conftest import (
    _make_company, _make_dividend, _make_financial, _make_price,
    _make_split, _make_stat,
)


@pytest.fixture
def populated_db(tmp_db: sqlite3.Connection) -> sqlite3.Connection:
    upsert_company(tmp_db, _make_company())
    upsert_company(tmp_db, _make_company(ticker="MSFT", name="Microsoft"))

    upsert_prices(tmp_db, [
        _make_price(date="2024-01-02", close=185.0),
        _make_price(date="2024-01-03", close=186.0),
        _make_price(date="2024-01-04", close=187.0),
    ])
    upsert_prices(tmp_db, [
        _make_price(ticker="MSFT", date="2024-01-02", close=370.0),
        _make_price(ticker="MSFT", date="2024-01-03", close=372.0),
    ])

    upsert_financials(tmp_db, [
        _make_financial(metric="Total Revenue", value=383_285e6, period_end="2023-09-30"),
        _make_financial(metric="Net Income", value=97_000e6, period_end="2023-09-30"),
        _make_financial(metric="Total Revenue", value=394_328e6, period_end="2022-09-30"),
    ])
    upsert_financials(tmp_db, [
        _make_financial(ticker="MSFT", metric="Total Revenue", value=211_915e6, period_end="2023-06-30"),
    ])

    upsert_dividends(tmp_db, [_make_dividend()])
    upsert_splits(tmp_db, [_make_split()])
    upsert_stats(tmp_db, _make_stat())

    return tmp_db


def test_get_prices(populated_db: sqlite3.Connection) -> None:
    q = YFinanceQuery(populated_db)
    df = q.get_prices("AAPL")
    assert len(df) == 3
    assert list(df.columns) == ["date", "open", "high", "low", "close", "volume"]


def test_get_prices_date_range(populated_db: sqlite3.Connection) -> None:
    q = YFinanceQuery(populated_db)
    df = q.get_prices("AAPL", start="2024-01-03", end="2024-01-03")
    assert len(df) == 1
    assert df.iloc[0]["close"] == 186.0


def test_get_company_info(populated_db: sqlite3.Connection) -> None:
    q = YFinanceQuery(populated_db)
    info = q.get_company_info("AAPL")
    assert info["name"] == "Apple Inc."
    assert info["ticker"] == "AAPL"


def test_get_company_info_unknown(populated_db: sqlite3.Connection) -> None:
    q = YFinanceQuery(populated_db)
    with pytest.raises(ValueError, match="Unknown ticker"):
        q.get_company_info("UNKNOWN")


def test_get_income_statement(populated_db: sqlite3.Connection) -> None:
    q = YFinanceQuery(populated_db)
    df = q.get_income_statement("AAPL")
    assert not df.empty
    assert "Total Revenue" in df.columns


def test_get_dividends(populated_db: sqlite3.Connection) -> None:
    q = YFinanceQuery(populated_db)
    df = q.get_dividends("AAPL")
    assert len(df) == 1
    assert df.iloc[0]["amount"] == 0.24


def test_get_splits(populated_db: sqlite3.Connection) -> None:
    q = YFinanceQuery(populated_db)
    df = q.get_splits("AAPL")
    assert len(df) == 1
    assert df.iloc[0]["ratio"] == 4.0


def test_get_stats(populated_db: sqlite3.Connection) -> None:
    q = YFinanceQuery(populated_db)
    df = q.get_stats("AAPL")
    assert len(df) == 1
    assert df.iloc[0]["pe_ratio"] == 30.5


def test_get_metric(populated_db: sqlite3.Connection) -> None:
    q = YFinanceQuery(populated_db)
    df = q.get_metric("AAPL", "Total Revenue")
    assert len(df) == 2


def test_compare(populated_db: sqlite3.Connection) -> None:
    q = YFinanceQuery(populated_db)
    df = q.compare(["AAPL", "MSFT"], "Total Revenue")
    assert "AAPL" in df.columns
    assert "MSFT" in df.columns


def test_compare_prices(populated_db: sqlite3.Connection) -> None:
    q = YFinanceQuery(populated_db)
    df = q.compare_prices(["AAPL", "MSFT"])
    assert "AAPL" in df.columns
    assert "MSFT" in df.columns
    assert len(df) == 3  # AAPL has 3 dates, MSFT 2 (NaN for missing)


def test_empty_results(tmp_db: sqlite3.Connection) -> None:
    q = YFinanceQuery(tmp_db)
    assert q.get_prices("NONEXIST").empty
    assert q.get_income_statement("NONEXIST").empty
    assert q.get_dividends("NONEXIST").empty
    assert q.get_splits("NONEXIST").empty
    assert q.compare(["NONEXIST"], "Revenue").empty
    assert q.compare_prices(["NONEXIST"]).empty
