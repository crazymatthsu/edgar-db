from __future__ import annotations

import sqlite3

from secmaster_db.db import get_db_stats, upsert_security

from .conftest import _make_security


def test_schema_creates_tables(tmp_db: sqlite3.Connection) -> None:
    cur = tmp_db.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    )
    tables = sorted(row[0] for row in cur.fetchall())
    assert "securities" in tables
    assert "metadata" in tables


def test_schema_version(tmp_db: sqlite3.Connection) -> None:
    cur = tmp_db.execute("SELECT value FROM metadata WHERE key = 'schema_version'")
    assert cur.fetchone()[0] == "1"


def test_upsert_security(tmp_db: sqlite3.Connection) -> None:
    sec = _make_security()
    upsert_security(tmp_db, sec)

    cur = tmp_db.execute("SELECT ticker, name FROM securities WHERE ticker = 'AAPL'")
    row = cur.fetchone()
    assert row == ("AAPL", "Apple Inc.")


def test_upsert_security_update(tmp_db: sqlite3.Connection) -> None:
    upsert_security(tmp_db, _make_security())
    upsert_security(tmp_db, _make_security(name="Apple Inc. Updated"))

    cur = tmp_db.execute("SELECT name FROM securities WHERE ticker = 'AAPL'")
    assert cur.fetchone()[0] == "Apple Inc. Updated"

    cur = tmp_db.execute("SELECT COUNT(*) FROM securities")
    assert cur.fetchone()[0] == 1


def test_upsert_security_preserves_fields(tmp_db: sqlite3.Connection) -> None:
    upsert_security(tmp_db, _make_security())

    cur = tmp_db.execute(
        "SELECT isin, figi, sector, style_box FROM securities WHERE ticker = 'AAPL'"
    )
    row = cur.fetchone()
    assert row == ("US0378331005", "BBG000B9XRY4", "Technology", "large_cap")


def test_get_db_stats(tmp_db: sqlite3.Connection) -> None:
    upsert_security(tmp_db, _make_security())
    upsert_security(tmp_db, _make_security(
        ticker="MSFT", name="Microsoft", sector="Technology",
        country="United States", isin="US5949181045", figi="BBG000BPH459",
    ))

    stats = get_db_stats(tmp_db)
    assert stats["securities"] == 2
    assert stats["sectors"] == 1
    assert stats["countries"] == 1
    assert stats["with_isin"] == 2
    assert stats["with_figi"] == 2


def test_get_db_stats_empty(tmp_db: sqlite3.Connection) -> None:
    stats = get_db_stats(tmp_db)
    assert stats["securities"] == 0
    assert stats["sectors"] == 0
