from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from .models import (
    CompanyRow, CompanyStatRow, DividendRow, FinancialRow, PriceRow, SplitRow,
)

SCHEMA_VERSION = "1"

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS metadata (
    key   TEXT PRIMARY KEY,
    value TEXT
);

CREATE TABLE IF NOT EXISTS companies (
    ticker           TEXT PRIMARY KEY,
    name             TEXT NOT NULL,
    sector           TEXT DEFAULT '',
    industry         TEXT DEFAULT '',
    market_cap       REAL DEFAULT 0,
    last_downloaded  TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS prices (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker   TEXT NOT NULL,
    date     TEXT NOT NULL,
    interval TEXT NOT NULL DEFAULT '1d',
    open     REAL NOT NULL,
    high     REAL NOT NULL,
    low      REAL NOT NULL,
    close    REAL NOT NULL,
    volume   INTEGER NOT NULL,
    FOREIGN KEY (ticker) REFERENCES companies(ticker)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_prices_dedup
    ON prices (ticker, date, interval);

CREATE TABLE IF NOT EXISTS company_stats (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker               TEXT NOT NULL,
    fetched_date         TEXT NOT NULL,
    market_cap           REAL DEFAULT 0,
    pe_ratio             REAL DEFAULT 0,
    forward_pe           REAL DEFAULT 0,
    peg_ratio            REAL DEFAULT 0,
    price_to_book        REAL DEFAULT 0,
    enterprise_value     REAL DEFAULT 0,
    ev_to_ebitda         REAL DEFAULT 0,
    profit_margin        REAL DEFAULT 0,
    operating_margin     REAL DEFAULT 0,
    roe                  REAL DEFAULT 0,
    roa                  REAL DEFAULT 0,
    revenue_growth       REAL DEFAULT 0,
    earnings_growth      REAL DEFAULT 0,
    dividend_yield       REAL DEFAULT 0,
    beta                 REAL DEFAULT 0,
    fifty_two_week_high  REAL DEFAULT 0,
    fifty_two_week_low   REAL DEFAULT 0,
    avg_volume           INTEGER DEFAULT 0,
    shares_outstanding   INTEGER DEFAULT 0,
    float_shares         INTEGER DEFAULT 0,
    short_ratio          REAL DEFAULT 0,
    FOREIGN KEY (ticker) REFERENCES companies(ticker)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_stats_dedup
    ON company_stats (ticker, fetched_date);

CREATE TABLE IF NOT EXISTS financials (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker      TEXT NOT NULL,
    statement   TEXT NOT NULL,
    period_type TEXT NOT NULL,
    period_end  TEXT NOT NULL,
    metric      TEXT NOT NULL,
    value       REAL NOT NULL,
    FOREIGN KEY (ticker) REFERENCES companies(ticker)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_financials_dedup
    ON financials (ticker, statement, period_type, period_end, metric);

CREATE INDEX IF NOT EXISTS idx_financials_ticker ON financials (ticker);
CREATE INDEX IF NOT EXISTS idx_financials_statement ON financials (ticker, statement);

CREATE TABLE IF NOT EXISTS dividends (
    id     INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker TEXT NOT NULL,
    date   TEXT NOT NULL,
    amount REAL NOT NULL,
    FOREIGN KEY (ticker) REFERENCES companies(ticker)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_dividends_dedup
    ON dividends (ticker, date);

CREATE TABLE IF NOT EXISTS splits (
    id     INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker TEXT NOT NULL,
    date   TEXT NOT NULL,
    ratio  REAL NOT NULL,
    FOREIGN KEY (ticker) REFERENCES companies(ticker)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_splits_dedup
    ON splits (ticker, date);
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


def upsert_company(conn: sqlite3.Connection, company: CompanyRow) -> None:
    conn.execute(
        """INSERT INTO companies (ticker, name, sector, industry, market_cap, last_downloaded)
           VALUES (?, ?, ?, ?, ?, ?)
           ON CONFLICT(ticker) DO UPDATE SET
               name=excluded.name,
               sector=excluded.sector,
               industry=excluded.industry,
               market_cap=excluded.market_cap,
               last_downloaded=excluded.last_downloaded
        """,
        (company.ticker, company.name, company.sector, company.industry,
         company.market_cap, company.last_downloaded),
    )
    conn.commit()


def upsert_prices(conn: sqlite3.Connection, prices: list[PriceRow]) -> int:
    if not prices:
        return 0
    inserted = 0
    for p in prices:
        conn.execute(
            """INSERT INTO prices (ticker, date, interval, open, high, low, close, volume)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(ticker, date, interval) DO UPDATE SET
                   open=excluded.open,
                   high=excluded.high,
                   low=excluded.low,
                   close=excluded.close,
                   volume=excluded.volume
            """,
            (p.ticker, p.date, p.interval, p.open, p.high, p.low, p.close, p.volume),
        )
        inserted += 1
    conn.commit()
    return inserted


def upsert_stats(conn: sqlite3.Connection, stat: CompanyStatRow) -> None:
    conn.execute(
        """INSERT INTO company_stats (
               ticker, fetched_date, market_cap, pe_ratio, forward_pe,
               peg_ratio, price_to_book, enterprise_value, ev_to_ebitda,
               profit_margin, operating_margin, roe, roa,
               revenue_growth, earnings_growth, dividend_yield, beta,
               fifty_two_week_high, fifty_two_week_low,
               avg_volume, shares_outstanding, float_shares, short_ratio
           ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
           ON CONFLICT(ticker, fetched_date) DO UPDATE SET
               market_cap=excluded.market_cap,
               pe_ratio=excluded.pe_ratio,
               forward_pe=excluded.forward_pe,
               peg_ratio=excluded.peg_ratio,
               price_to_book=excluded.price_to_book,
               enterprise_value=excluded.enterprise_value,
               ev_to_ebitda=excluded.ev_to_ebitda,
               profit_margin=excluded.profit_margin,
               operating_margin=excluded.operating_margin,
               roe=excluded.roe,
               roa=excluded.roa,
               revenue_growth=excluded.revenue_growth,
               earnings_growth=excluded.earnings_growth,
               dividend_yield=excluded.dividend_yield,
               beta=excluded.beta,
               fifty_two_week_high=excluded.fifty_two_week_high,
               fifty_two_week_low=excluded.fifty_two_week_low,
               avg_volume=excluded.avg_volume,
               shares_outstanding=excluded.shares_outstanding,
               float_shares=excluded.float_shares,
               short_ratio=excluded.short_ratio
        """,
        (stat.ticker, stat.fetched_date, stat.market_cap, stat.pe_ratio,
         stat.forward_pe, stat.peg_ratio, stat.price_to_book,
         stat.enterprise_value, stat.ev_to_ebitda, stat.profit_margin,
         stat.operating_margin, stat.roe, stat.roa, stat.revenue_growth,
         stat.earnings_growth, stat.dividend_yield, stat.beta,
         stat.fifty_two_week_high, stat.fifty_two_week_low,
         stat.avg_volume, stat.shares_outstanding, stat.float_shares,
         stat.short_ratio),
    )
    conn.commit()


def upsert_financials(conn: sqlite3.Connection, rows: list[FinancialRow]) -> int:
    if not rows:
        return 0
    inserted = 0
    for r in rows:
        conn.execute(
            """INSERT INTO financials (ticker, statement, period_type, period_end, metric, value)
               VALUES (?, ?, ?, ?, ?, ?)
               ON CONFLICT(ticker, statement, period_type, period_end, metric) DO UPDATE SET
                   value=excluded.value
            """,
            (r.ticker, r.statement, r.period_type, r.period_end, r.metric, r.value),
        )
        inserted += 1
    conn.commit()
    return inserted


def upsert_dividends(conn: sqlite3.Connection, rows: list[DividendRow]) -> int:
    if not rows:
        return 0
    inserted = 0
    for r in rows:
        conn.execute(
            """INSERT INTO dividends (ticker, date, amount)
               VALUES (?, ?, ?)
               ON CONFLICT(ticker, date) DO UPDATE SET amount=excluded.amount
            """,
            (r.ticker, r.date, r.amount),
        )
        inserted += 1
    conn.commit()
    return inserted


def upsert_splits(conn: sqlite3.Connection, rows: list[SplitRow]) -> int:
    if not rows:
        return 0
    inserted = 0
    for r in rows:
        conn.execute(
            """INSERT INTO splits (ticker, date, ratio)
               VALUES (?, ?, ?)
               ON CONFLICT(ticker, date) DO UPDATE SET ratio=excluded.ratio
            """,
            (r.ticker, r.date, r.ratio),
        )
        inserted += 1
    conn.commit()
    return inserted


def get_db_stats(conn: sqlite3.Connection) -> dict[str, Any]:
    stats: dict[str, Any] = {}
    cur = conn.execute("SELECT COUNT(*) FROM companies")
    stats["companies"] = cur.fetchone()[0]
    cur = conn.execute("SELECT COUNT(*) FROM prices")
    stats["prices"] = cur.fetchone()[0]
    cur = conn.execute("SELECT COUNT(*) FROM financials")
    stats["financials"] = cur.fetchone()[0]
    cur = conn.execute("SELECT COUNT(*) FROM company_stats")
    stats["stat_snapshots"] = cur.fetchone()[0]
    cur = conn.execute("SELECT COUNT(*) FROM dividends")
    stats["dividends"] = cur.fetchone()[0]
    cur = conn.execute("SELECT COUNT(*) FROM splits")
    stats["splits"] = cur.fetchone()[0]
    return stats
