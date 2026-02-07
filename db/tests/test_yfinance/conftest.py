from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from yfinance_db.db import connect_db
from yfinance_db.models import (
    CompanyRow, CompanyStatRow, DividendRow, FinancialRow, PriceRow, SplitRow,
)


@pytest.fixture
def tmp_db(tmp_path: Path) -> sqlite3.Connection:
    db_path = tmp_path / "test.db"
    return connect_db(db_path)


def _make_company(**overrides: object) -> CompanyRow:
    defaults = dict(
        ticker="AAPL",
        name="Apple Inc.",
        sector="Technology",
        industry="Consumer Electronics",
        market_cap=3_000_000_000_000.0,
        last_downloaded="2024-01-01T00:00:00+00:00",
    )
    defaults.update(overrides)
    return CompanyRow(**defaults)


def _make_price(**overrides: object) -> PriceRow:
    defaults = dict(
        ticker="AAPL",
        date="2024-01-02",
        interval="1d",
        open=185.0,
        high=186.0,
        low=184.0,
        close=185.5,
        volume=50_000_000,
    )
    defaults.update(overrides)
    return PriceRow(**defaults)


def _make_financial(**overrides: object) -> FinancialRow:
    defaults = dict(
        ticker="AAPL",
        statement="income",
        period_type="annual",
        period_end="2023-09-30",
        metric="Total Revenue",
        value=383_285_000_000.0,
    )
    defaults.update(overrides)
    return FinancialRow(**defaults)


def _make_stat(**overrides: object) -> CompanyStatRow:
    defaults = dict(
        ticker="AAPL",
        fetched_date="2024-01-01",
        market_cap=3_000_000_000_000.0,
        pe_ratio=30.5,
        forward_pe=28.0,
    )
    defaults.update(overrides)
    return CompanyStatRow(**defaults)


def _make_dividend(**overrides: object) -> DividendRow:
    defaults = dict(ticker="AAPL", date="2024-01-15", amount=0.24)
    defaults.update(overrides)
    return DividendRow(**defaults)


def _make_split(**overrides: object) -> SplitRow:
    defaults = dict(ticker="AAPL", date="2020-08-31", ratio=4.0)
    defaults.update(overrides)
    return SplitRow(**defaults)
