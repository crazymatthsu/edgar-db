from __future__ import annotations

import sqlite3

from yfinance_db.db import (
    get_db_stats, upsert_company, upsert_dividends, upsert_financials,
    upsert_prices, upsert_splits, upsert_stats,
)

from .conftest import (
    _make_company, _make_dividend, _make_financial, _make_price,
    _make_split, _make_stat,
)


def test_schema_creates_tables(tmp_db: sqlite3.Connection) -> None:
    cur = tmp_db.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    )
    tables = sorted(row[0] for row in cur.fetchall())
    assert "companies" in tables
    assert "prices" in tables
    assert "financials" in tables
    assert "company_stats" in tables
    assert "dividends" in tables
    assert "splits" in tables
    assert "metadata" in tables


def test_schema_version(tmp_db: sqlite3.Connection) -> None:
    cur = tmp_db.execute("SELECT value FROM metadata WHERE key = 'schema_version'")
    assert cur.fetchone()[0] == "1"


def test_upsert_company(tmp_db: sqlite3.Connection) -> None:
    company = _make_company()
    upsert_company(tmp_db, company)

    cur = tmp_db.execute("SELECT ticker, name FROM companies WHERE ticker = 'AAPL'")
    row = cur.fetchone()
    assert row == ("AAPL", "Apple Inc.")

    # Upsert with updated name
    company2 = _make_company(name="Apple Inc. Updated")
    upsert_company(tmp_db, company2)

    cur = tmp_db.execute("SELECT name FROM companies WHERE ticker = 'AAPL'")
    assert cur.fetchone()[0] == "Apple Inc. Updated"


def test_upsert_prices(tmp_db: sqlite3.Connection) -> None:
    upsert_company(tmp_db, _make_company())
    prices = [_make_price(), _make_price(date="2024-01-03", close=186.0)]
    count = upsert_prices(tmp_db, prices)
    assert count == 2

    cur = tmp_db.execute("SELECT COUNT(*) FROM prices WHERE ticker = 'AAPL'")
    assert cur.fetchone()[0] == 2


def test_upsert_prices_dedup(tmp_db: sqlite3.Connection) -> None:
    upsert_company(tmp_db, _make_company())
    prices = [_make_price(close=185.0)]
    upsert_prices(tmp_db, prices)

    # Upsert same date with different close
    prices2 = [_make_price(close=190.0)]
    upsert_prices(tmp_db, prices2)

    cur = tmp_db.execute("SELECT COUNT(*) FROM prices WHERE ticker = 'AAPL'")
    assert cur.fetchone()[0] == 1

    cur = tmp_db.execute("SELECT close FROM prices WHERE ticker = 'AAPL'")
    assert cur.fetchone()[0] == 190.0


def test_upsert_financials(tmp_db: sqlite3.Connection) -> None:
    upsert_company(tmp_db, _make_company())
    rows = [
        _make_financial(metric="Total Revenue"),
        _make_financial(metric="Net Income", value=97_000_000_000.0),
    ]
    count = upsert_financials(tmp_db, rows)
    assert count == 2


def test_upsert_financials_dedup(tmp_db: sqlite3.Connection) -> None:
    upsert_company(tmp_db, _make_company())
    upsert_financials(tmp_db, [_make_financial(value=100.0)])
    upsert_financials(tmp_db, [_make_financial(value=200.0)])

    cur = tmp_db.execute("SELECT COUNT(*) FROM financials WHERE ticker = 'AAPL'")
    assert cur.fetchone()[0] == 1

    cur = tmp_db.execute("SELECT value FROM financials WHERE ticker = 'AAPL'")
    assert cur.fetchone()[0] == 200.0


def test_upsert_stats(tmp_db: sqlite3.Connection) -> None:
    upsert_company(tmp_db, _make_company())
    upsert_stats(tmp_db, _make_stat())

    cur = tmp_db.execute("SELECT pe_ratio FROM company_stats WHERE ticker = 'AAPL'")
    assert cur.fetchone()[0] == 30.5


def test_upsert_dividends(tmp_db: sqlite3.Connection) -> None:
    upsert_company(tmp_db, _make_company())
    count = upsert_dividends(tmp_db, [_make_dividend()])
    assert count == 1


def test_upsert_splits(tmp_db: sqlite3.Connection) -> None:
    upsert_company(tmp_db, _make_company())
    count = upsert_splits(tmp_db, [_make_split()])
    assert count == 1


def test_get_db_stats(tmp_db: sqlite3.Connection) -> None:
    upsert_company(tmp_db, _make_company())
    upsert_prices(tmp_db, [_make_price()])
    upsert_financials(tmp_db, [_make_financial()])
    upsert_dividends(tmp_db, [_make_dividend()])
    upsert_splits(tmp_db, [_make_split()])

    stats = get_db_stats(tmp_db)
    assert stats["companies"] == 1
    assert stats["prices"] == 1
    assert stats["financials"] == 1
    assert stats["dividends"] == 1
    assert stats["splits"] == 1


def test_upsert_empty_lists(tmp_db: sqlite3.Connection) -> None:
    assert upsert_prices(tmp_db, []) == 0
    assert upsert_financials(tmp_db, []) == 0
    assert upsert_dividends(tmp_db, []) == 0
    assert upsert_splits(tmp_db, []) == 0
