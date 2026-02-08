from __future__ import annotations

import sqlite3

import pytest

from secmaster_db.db import upsert_security
from secmaster_db.query import SecMasterQuery

from .conftest import _make_security


@pytest.fixture
def populated_db(tmp_db: sqlite3.Connection) -> sqlite3.Connection:
    upsert_security(tmp_db, _make_security())
    upsert_security(tmp_db, _make_security(
        ticker="MSFT", name="Microsoft Corp.", sector="Technology",
        industry="Software", country="United States",
        market_cap=2_800_000_000_000.0, style_box="large_cap",
        isin="US5949181045",
    ))
    upsert_security(tmp_db, _make_security(
        ticker="JNJ", name="Johnson & Johnson", sector="Healthcare",
        industry="Pharmaceuticals", country="United States",
        market_cap=400_000_000_000.0, style_box="large_cap",
    ))
    upsert_security(tmp_db, _make_security(
        ticker="SMCO", name="Small Company", sector="Healthcare",
        industry="Biotech", country="Canada",
        market_cap=500_000_000.0, style_box="small_cap",
    ))
    return tmp_db


def test_get_security(populated_db: sqlite3.Connection) -> None:
    q = SecMasterQuery(populated_db)
    sec = q.get_security("AAPL")
    assert sec is not None
    assert sec.ticker == "AAPL"
    assert sec.name == "Apple Inc."
    assert sec.sector == "Technology"
    assert sec.style_box == "large_cap"


def test_get_security_case_insensitive(populated_db: sqlite3.Connection) -> None:
    q = SecMasterQuery(populated_db)
    sec = q.get_security("aapl")
    assert sec is not None
    assert sec.ticker == "AAPL"


def test_get_security_not_found(populated_db: sqlite3.Connection) -> None:
    q = SecMasterQuery(populated_db)
    assert q.get_security("NONEXIST") is None


def test_list_all(populated_db: sqlite3.Connection) -> None:
    q = SecMasterQuery(populated_db)
    df = q.list_all()
    assert len(df) == 4
    assert list(df["ticker"]) == ["AAPL", "JNJ", "MSFT", "SMCO"]


def test_search_by_sector(populated_db: sqlite3.Connection) -> None:
    q = SecMasterQuery(populated_db)
    df = q.search(sector="Technology")
    assert len(df) == 2
    assert set(df["ticker"]) == {"AAPL", "MSFT"}


def test_search_by_style_box(populated_db: sqlite3.Connection) -> None:
    q = SecMasterQuery(populated_db)
    df = q.search(style_box="small_cap")
    assert len(df) == 1
    assert df.iloc[0]["ticker"] == "SMCO"


def test_search_by_country(populated_db: sqlite3.Connection) -> None:
    q = SecMasterQuery(populated_db)
    df = q.search(country="Canada")
    assert len(df) == 1
    assert df.iloc[0]["ticker"] == "SMCO"


def test_search_combined(populated_db: sqlite3.Connection) -> None:
    q = SecMasterQuery(populated_db)
    df = q.search(sector="Healthcare", country="United States")
    assert len(df) == 1
    assert df.iloc[0]["ticker"] == "JNJ"


def test_search_no_results(populated_db: sqlite3.Connection) -> None:
    q = SecMasterQuery(populated_db)
    df = q.search(sector="Energy")
    assert df.empty


def test_list_by_sector(populated_db: sqlite3.Connection) -> None:
    q = SecMasterQuery(populated_db)
    df = q.list_by_sector()
    assert len(df) == 2
    assert "Technology" in df["sector"].values
    assert "Healthcare" in df["sector"].values


def test_list_by_style_box(populated_db: sqlite3.Connection) -> None:
    q = SecMasterQuery(populated_db)
    df = q.list_by_style_box()
    assert len(df) == 2
    assert "large_cap" in df["style_box"].values
    assert "small_cap" in df["style_box"].values


def test_empty_db(tmp_db: sqlite3.Connection) -> None:
    q = SecMasterQuery(tmp_db)
    assert q.get_security("AAPL") is None
    assert q.list_all().empty
    assert q.search(sector="Technology").empty
    assert q.list_by_sector().empty
