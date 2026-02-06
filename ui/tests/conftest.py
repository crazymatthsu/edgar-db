"""Test fixtures for the UI module tests."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from edgar_db.db import connect_db, upsert_company, upsert_facts, upsert_ticker_map
from edgar_db.models import Company, FactRow
from ui.backend.app import app
from ui.backend.dependencies import close_conn, set_db_path

# Re-export for use in test files
_conn_ref: sqlite3.Connection | None = None


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
def seeded_db(tmp_path: Path) -> sqlite3.Connection:
    """Create a seeded DB with AAPL and MSFT sample data."""
    db_path = tmp_path / "test.db"
    # Use connect_db for schema init, then reopen with check_same_thread=False
    # so the connection works across TestClient threads
    init_conn = connect_db(db_path)
    init_conn.close()
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")

    upsert_ticker_map(conn, {"AAPL": 320193, "MSFT": 789019})
    upsert_company(conn, Company(cik=320193, name="Apple Inc.", ticker="AAPL"))
    upsert_company(conn, Company(cik=789019, name="Microsoft Corp", ticker="MSFT"))

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
    upsert_facts(conn, facts)

    return conn


@pytest.fixture
def client(seeded_db: sqlite3.Connection, tmp_path: Path) -> TestClient:
    """FastAPI test client with seeded database."""
    import ui.backend.dependencies as deps

    db_path = tmp_path / "test.db"
    # Inject the seeded connection into the dependency module
    deps._conn = seeded_db
    deps._db_path = db_path

    yield TestClient(app, raise_server_exceptions=False)

    # Cleanup
    deps._conn = None
    deps._db_path = None
