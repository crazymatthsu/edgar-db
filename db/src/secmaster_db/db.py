from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .models import SecurityRow

SCHEMA_VERSION = "2"

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

CREATE TABLE IF NOT EXISTS index_components (
    index_code   TEXT NOT NULL,
    ticker       TEXT NOT NULL,
    last_updated TEXT DEFAULT '',
    PRIMARY KEY (index_code, ticker)
);
"""

_V2_MIGRATION_SQL = """
CREATE TABLE IF NOT EXISTS index_components (
    index_code   TEXT NOT NULL,
    ticker       TEXT NOT NULL,
    last_updated TEXT DEFAULT '',
    PRIMARY KEY (index_code, ticker)
);
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
    else:
        _maybe_migrate(conn)


def _maybe_migrate(conn: sqlite3.Connection) -> None:
    cur = conn.execute("SELECT value FROM metadata WHERE key = 'schema_version'")
    row = cur.fetchone()
    version = row[0] if row else "1"

    if version < "2":
        conn.executescript(_V2_MIGRATION_SQL)
        conn.execute(
            "INSERT OR REPLACE INTO metadata (key, value) VALUES (?, ?)",
            ("schema_version", "2"),
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


def upsert_index_components(
    conn: sqlite3.Connection,
    index_code: str,
    tickers: list[str],
    last_updated: str | None = None,
) -> None:
    """Replace all components for *index_code* with the given ticker list."""
    if last_updated is None:
        last_updated = datetime.now(timezone.utc).isoformat()
    conn.execute("DELETE FROM index_components WHERE index_code = ?", (index_code,))
    conn.executemany(
        "INSERT INTO index_components (index_code, ticker, last_updated) VALUES (?, ?, ?)",
        [(index_code, t, last_updated) for t in tickers],
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

    # Index component counts
    cur = conn.execute(
        "SELECT index_code, COUNT(*) FROM index_components GROUP BY index_code ORDER BY index_code"
    )
    stats["indexes"] = {row[0]: row[1] for row in cur.fetchall()}

    return stats
