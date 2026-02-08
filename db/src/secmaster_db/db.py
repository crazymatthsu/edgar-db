from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from .models import SecurityRow

SCHEMA_VERSION = "1"

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS metadata (
    key   TEXT PRIMARY KEY,
    value TEXT
);

CREATE TABLE IF NOT EXISTS securities (
    ticker             TEXT PRIMARY KEY,
    name               TEXT NOT NULL DEFAULT '',
    isin               TEXT DEFAULT '',
    cusip              TEXT DEFAULT '',
    sedol              TEXT DEFAULT '',
    primary_ric        TEXT DEFAULT '',
    bloomberg_code     TEXT DEFAULT '',
    figi               TEXT DEFAULT '',
    share_class_figi   TEXT DEFAULT '',
    shares_outstanding INTEGER DEFAULT 0,
    country            TEXT DEFAULT '',
    exchange_mic       TEXT DEFAULT '',
    exchange_currency  TEXT DEFAULT '',
    sector             TEXT DEFAULT '',
    industry           TEXT DEFAULT '',
    market_cap         REAL DEFAULT 0,
    style_box          TEXT DEFAULT '',
    last_updated       TEXT DEFAULT ''
);

CREATE INDEX IF NOT EXISTS idx_securities_sector ON securities (sector);
CREATE INDEX IF NOT EXISTS idx_securities_industry ON securities (industry);
CREATE INDEX IF NOT EXISTS idx_securities_style_box ON securities (style_box);
CREATE INDEX IF NOT EXISTS idx_securities_country ON securities (country);
CREATE INDEX IF NOT EXISTS idx_securities_isin ON securities (isin);
"""


def connect_db(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    _init_schema(conn)
    return conn


def _init_schema(conn: sqlite3.Connection) -> None:
    cur = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='metadata'"
    )
    if cur.fetchone() is None:
        conn.executescript(_SCHEMA_SQL)
        conn.execute(
            "INSERT OR REPLACE INTO metadata (key, value) VALUES (?, ?)",
            ("schema_version", SCHEMA_VERSION),
        )
        conn.commit()


def upsert_security(conn: sqlite3.Connection, sec: SecurityRow) -> None:
    conn.execute(
        """INSERT INTO securities (
               ticker, name, isin, cusip, sedol, primary_ric, bloomberg_code,
               figi, share_class_figi, shares_outstanding,
               country, exchange_mic, exchange_currency,
               sector, industry, market_cap, style_box, last_updated
           ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
           ON CONFLICT(ticker) DO UPDATE SET
               name=excluded.name,
               isin=excluded.isin,
               cusip=excluded.cusip,
               sedol=excluded.sedol,
               primary_ric=excluded.primary_ric,
               bloomberg_code=excluded.bloomberg_code,
               figi=excluded.figi,
               share_class_figi=excluded.share_class_figi,
               shares_outstanding=excluded.shares_outstanding,
               country=excluded.country,
               exchange_mic=excluded.exchange_mic,
               exchange_currency=excluded.exchange_currency,
               sector=excluded.sector,
               industry=excluded.industry,
               market_cap=excluded.market_cap,
               style_box=excluded.style_box,
               last_updated=excluded.last_updated
        """,
        (sec.ticker, sec.name, sec.isin, sec.cusip, sec.sedol,
         sec.primary_ric, sec.bloomberg_code, sec.figi, sec.share_class_figi,
         sec.shares_outstanding, sec.country, sec.exchange_mic,
         sec.exchange_currency, sec.sector, sec.industry,
         sec.market_cap, sec.style_box, sec.last_updated),
    )
    conn.commit()


def get_db_stats(conn: sqlite3.Connection) -> dict[str, Any]:
    stats: dict[str, Any] = {}
    cur = conn.execute("SELECT COUNT(*) FROM securities")
    stats["securities"] = cur.fetchone()[0]
    cur = conn.execute("SELECT COUNT(DISTINCT sector) FROM securities WHERE sector != ''")
    stats["sectors"] = cur.fetchone()[0]
    cur = conn.execute("SELECT COUNT(DISTINCT country) FROM securities WHERE country != ''")
    stats["countries"] = cur.fetchone()[0]
    cur = conn.execute("SELECT COUNT(*) FROM securities WHERE isin != ''")
    stats["with_isin"] = cur.fetchone()[0]
    cur = conn.execute("SELECT COUNT(*) FROM securities WHERE figi != ''")
    stats["with_figi"] = cur.fetchone()[0]
    return stats
