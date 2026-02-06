"""Tests for the DataFrame query API."""

from __future__ import annotations

import sqlite3

import pytest

from edgar_db.db import upsert_company, upsert_facts, upsert_ticker_map
from edgar_db.models import Company, FactRow
from edgar_db.query import EdgarQuery


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


@pytest.fixture
def query_db(tmp_db: sqlite3.Connection) -> EdgarQuery:
    """Set up a DB with sample data and return an EdgarQuery."""
    upsert_ticker_map(tmp_db, {"AAPL": 320193, "MSFT": 789019})
    upsert_company(tmp_db, Company(cik=320193, name="Apple Inc.", ticker="AAPL"))
    upsert_company(tmp_db, Company(cik=789019, name="Microsoft Corp", ticker="MSFT"))

    facts = [
        # AAPL income statement
        _make_fact(canonical_name="revenue", value=383285000000, fiscal_year=2023),
        _make_fact(canonical_name="revenue", value=394328000000, fiscal_year=2022, period_end="2022-09-24"),
        _make_fact(canonical_name="net_income", value=96995000000, fiscal_year=2023),
        _make_fact(canonical_name="net_income", value=99803000000, fiscal_year=2022, period_end="2022-09-24"),
        _make_fact(canonical_name="cost_of_revenue", tag="CostOfGoodsAndServicesSold",
                   value=214137000000, fiscal_year=2023),
        # AAPL balance sheet
        _make_fact(canonical_name="total_assets", tag="Assets", statement="balance",
                   value=352583000000, fiscal_year=2023),
        # AAPL cash flow
        _make_fact(canonical_name="operating_cash_flow",
                   tag="NetCashProvidedByUsedInOperatingActivities",
                   statement="cashflow", value=110543000000, fiscal_year=2023),
        _make_fact(canonical_name="capital_expenditure",
                   tag="PaymentsToAcquirePropertyPlantAndEquipment",
                   statement="cashflow", value=11006000000, fiscal_year=2023),
        # MSFT income
        _make_fact(cik=789019, canonical_name="revenue", value=211900000000,
                   fiscal_year=2023, tag="Revenues"),
        _make_fact(cik=789019, canonical_name="net_income", value=72361000000,
                   fiscal_year=2023),
        # Quarterly data
        _make_fact(canonical_name="revenue", value=94836000000,
                   fiscal_year=2023, fiscal_period="Q2", form="10-Q",
                   period_end="2023-04-01"),
    ]
    upsert_facts(tmp_db, facts)
    return EdgarQuery(tmp_db)


class TestGetIncomeStatement:
    def test_returns_dataframe(self, query_db: EdgarQuery) -> None:
        df = query_db.get_income_statement("AAPL")
        assert not df.empty
        assert "revenue" in df.columns
        assert "net_income" in df.columns

    def test_annual_only(self, query_db: EdgarQuery) -> None:
        df = query_db.get_income_statement("AAPL", period="annual")
        assert all(df["fiscal_period"] == "FY")

    def test_quarterly(self, query_db: EdgarQuery) -> None:
        df = query_db.get_income_statement("AAPL", period="quarterly")
        assert not df.empty
        assert all(df["fiscal_period"] != "FY")

    def test_sorted_desc(self, query_db: EdgarQuery) -> None:
        df = query_db.get_income_statement("AAPL")
        dates = df["period_end"].tolist()
        assert dates == sorted(dates, reverse=True)


class TestGetBalanceSheet:
    def test_returns_data(self, query_db: EdgarQuery) -> None:
        df = query_db.get_balance_sheet("AAPL")
        assert not df.empty
        assert "total_assets" in df.columns


class TestGetCashFlow:
    def test_computes_free_cash_flow(self, query_db: EdgarQuery) -> None:
        df = query_db.get_cash_flow("AAPL")
        assert "free_cash_flow" in df.columns
        row = df.iloc[0]
        expected = row["operating_cash_flow"] - row["capital_expenditure"]
        assert row["free_cash_flow"] == expected


class TestGetMetric:
    def test_single_metric(self, query_db: EdgarQuery) -> None:
        df = query_db.get_metric("AAPL", "revenue")
        assert len(df) == 2  # 2 annual years
        assert "value" in df.columns

    def test_unknown_ticker(self, query_db: EdgarQuery) -> None:
        with pytest.raises(ValueError, match="Unknown ticker"):
            query_db.get_metric("ZZZZ", "revenue")


class TestCompare:
    def test_compare_tickers(self, query_db: EdgarQuery) -> None:
        df = query_db.compare(["AAPL", "MSFT"], "revenue")
        assert "AAPL" in df.columns
        assert "MSFT" in df.columns
        assert not df.empty

    def test_compare_empty(self, query_db: EdgarQuery) -> None:
        df = query_db.compare(["ZZZZ"], "revenue")
        assert df.empty
