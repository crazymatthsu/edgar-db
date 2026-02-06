"""Tests for SQLite database operations."""

from __future__ import annotations

import sqlite3

from edgar_db.db import (
    get_db_stats,
    query_facts_df,
    resolve_cik,
    upsert_company,
    upsert_facts,
    upsert_ticker_map,
)
from edgar_db.models import Company, FactRow


def _make_fact(**overrides) -> FactRow:
    defaults = dict(
        cik=320193,
        tag="Revenues",
        canonical_name="revenue",
        statement="income",
        value=100000.0,
        unit="USD",
        period_end="2023-09-30",
        fiscal_year=2023,
        fiscal_period="FY",
        form="10-K",
        filed="2023-11-03",
        accession="0000320193-23-000106",
    )
    defaults.update(overrides)
    return FactRow(**defaults)


class TestSchema:
    def test_tables_created(self, tmp_db: sqlite3.Connection) -> None:
        cur = tmp_db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        tables = {row[0] for row in cur.fetchall()}
        assert "companies" in tables
        assert "facts" in tables
        assert "ticker_map" in tables
        assert "metadata" in tables

    def test_schema_version(self, tmp_db: sqlite3.Connection) -> None:
        cur = tmp_db.execute("SELECT value FROM metadata WHERE key='schema_version'")
        assert cur.fetchone()[0] == "1"


class TestUpsertCompany:
    def test_insert(self, tmp_db: sqlite3.Connection) -> None:
        c = Company(cik=320193, name="Apple Inc.", ticker="AAPL")
        upsert_company(tmp_db, c)
        cur = tmp_db.execute("SELECT name, ticker FROM companies WHERE cik=320193")
        row = cur.fetchone()
        assert row == ("Apple Inc.", "AAPL")

    def test_upsert_updates(self, tmp_db: sqlite3.Connection) -> None:
        c1 = Company(cik=320193, name="Apple Inc.", ticker="AAPL")
        upsert_company(tmp_db, c1)
        c2 = Company(cik=320193, name="Apple Inc. Updated", ticker="AAPL", last_downloaded="2024-01-01")
        upsert_company(tmp_db, c2)
        cur = tmp_db.execute("SELECT name, last_downloaded FROM companies WHERE cik=320193")
        row = cur.fetchone()
        assert row == ("Apple Inc. Updated", "2024-01-01")


class TestUpsertFacts:
    def test_insert_facts(self, tmp_db: sqlite3.Connection) -> None:
        upsert_company(tmp_db, Company(cik=320193, name="Apple", ticker="AAPL"))
        facts = [_make_fact(), _make_fact(canonical_name="net_income", value=50000.0)]
        count = upsert_facts(tmp_db, facts)
        assert count == 2

    def test_dedup_on_conflict(self, tmp_db: sqlite3.Connection) -> None:
        upsert_company(tmp_db, Company(cik=320193, name="Apple", ticker="AAPL"))
        f1 = _make_fact(value=100000.0)
        upsert_facts(tmp_db, [f1])
        f2 = _make_fact(value=200000.0)  # Same dedup key, different value
        upsert_facts(tmp_db, [f2])
        cur = tmp_db.execute("SELECT value FROM facts WHERE canonical_name='revenue'")
        assert cur.fetchone()[0] == 200000.0  # Updated
        assert tmp_db.execute("SELECT COUNT(*) FROM facts").fetchone()[0] == 1

    def test_empty_list(self, tmp_db: sqlite3.Connection) -> None:
        assert upsert_facts(tmp_db, []) == 0


class TestTickerMap:
    def test_upsert_and_resolve(self, tmp_db: sqlite3.Connection) -> None:
        upsert_ticker_map(tmp_db, {"AAPL": 320193, "MSFT": 789019})
        assert resolve_cik(tmp_db, "AAPL") == 320193
        assert resolve_cik(tmp_db, "aapl") == 320193  # Case insensitive
        assert resolve_cik(tmp_db, "MSFT") == 789019
        assert resolve_cik(tmp_db, "UNKNOWN") is None


class TestQueryFactsDf:
    def test_query_annual(self, tmp_db: sqlite3.Connection) -> None:
        upsert_company(tmp_db, Company(cik=320193, name="Apple", ticker="AAPL"))
        facts = [
            _make_fact(form="10-K", fiscal_year=2023),
            _make_fact(form="10-Q", fiscal_year=2023, fiscal_period="Q1", period_end="2023-01-01"),
        ]
        upsert_facts(tmp_db, facts)
        df = query_facts_df(tmp_db, 320193, period="annual")
        assert len(df) == 1
        assert df.iloc[0]["form"] == "10-K"

    def test_query_by_statement(self, tmp_db: sqlite3.Connection) -> None:
        upsert_company(tmp_db, Company(cik=320193, name="Apple", ticker="AAPL"))
        facts = [
            _make_fact(statement="income"),
            _make_fact(statement="balance", canonical_name="total_assets", period_end="2023-09-29"),
        ]
        upsert_facts(tmp_db, facts)
        df = query_facts_df(tmp_db, 320193, statement="income", period="annual")
        assert len(df) == 1
        assert df.iloc[0]["statement"] == "income"


class TestDbStats:
    def test_stats(self, tmp_db: sqlite3.Connection) -> None:
        upsert_company(tmp_db, Company(cik=320193, name="Apple", ticker="AAPL"))
        upsert_facts(tmp_db, [_make_fact()])
        upsert_ticker_map(tmp_db, {"AAPL": 320193})
        stats = get_db_stats(tmp_db)
        assert stats["companies"] == 1
        assert stats["facts"] == 1
        assert stats["tickers"] == 1
