from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

import pandas as pd

from .models import Company, FactRow

SCHEMA_VERSION = "1"

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS metadata (
    key   TEXT PRIMARY KEY,
    value TEXT
);

CREATE TABLE IF NOT EXISTS companies (
    cik              INTEGER PRIMARY KEY,
    name             TEXT NOT NULL,
    ticker           TEXT NOT NULL,
    sic              TEXT DEFAULT '',
    exchanges        TEXT DEFAULT '',
    last_downloaded  TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS ticker_map (
    ticker  TEXT PRIMARY KEY,
    cik     INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS facts (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    cik             INTEGER NOT NULL,
    tag             TEXT NOT NULL,
    canonical_name  TEXT NOT NULL,
    statement       TEXT NOT NULL,
    value           REAL NOT NULL,
    unit            TEXT NOT NULL,
    period_end      TEXT NOT NULL,
    fiscal_year     INTEGER NOT NULL,
    fiscal_period   TEXT NOT NULL,
    form            TEXT NOT NULL,
    filed           TEXT NOT NULL,
    accession       TEXT NOT NULL,
    FOREIGN KEY (cik) REFERENCES companies(cik)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_facts_dedup
    ON facts (cik, canonical_name, period_end, fiscal_period, form);

CREATE INDEX IF NOT EXISTS idx_facts_cik ON facts (cik);
CREATE INDEX IF NOT EXISTS idx_facts_statement ON facts (cik, statement);
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


def upsert_company(conn: sqlite3.Connection, company: Company) -> None:
    conn.execute(
        """INSERT INTO companies (cik, name, ticker, sic, exchanges, last_downloaded)
           VALUES (?, ?, ?, ?, ?, ?)
           ON CONFLICT(cik) DO UPDATE SET
               name=excluded.name,
               ticker=excluded.ticker,
               sic=excluded.sic,
               exchanges=excluded.exchanges,
               last_downloaded=excluded.last_downloaded
        """,
        (company.cik, company.name, company.ticker, company.sic,
         company.exchanges, company.last_downloaded),
    )
    conn.commit()


def upsert_facts(conn: sqlite3.Connection, facts: list[FactRow]) -> int:
    if not facts:
        return 0
    inserted = 0
    for fact in facts:
        try:
            conn.execute(
                """INSERT INTO facts
                   (cik, tag, canonical_name, statement, value, unit,
                    period_end, fiscal_year, fiscal_period, form, filed, accession)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(cik, canonical_name, period_end, fiscal_period, form)
                   DO UPDATE SET
                       value=excluded.value,
                       tag=excluded.tag,
                       unit=excluded.unit,
                       filed=excluded.filed,
                       accession=excluded.accession
                """,
                (fact.cik, fact.tag, fact.canonical_name, fact.statement,
                 fact.value, fact.unit, fact.period_end, fact.fiscal_year,
                 fact.fiscal_period, fact.form, fact.filed, fact.accession),
            )
            inserted += 1
        except sqlite3.IntegrityError:
            pass
    conn.commit()
    return inserted


def upsert_ticker_map(conn: sqlite3.Connection, mappings: dict[str, int]) -> None:
    conn.executemany(
        "INSERT OR REPLACE INTO ticker_map (ticker, cik) VALUES (?, ?)",
        [(ticker, cik) for ticker, cik in mappings.items()],
    )
    conn.commit()


def resolve_cik(conn: sqlite3.Connection, ticker: str) -> int | None:
    cur = conn.execute(
        "SELECT cik FROM ticker_map WHERE ticker = ? COLLATE NOCASE", (ticker.upper(),)
    )
    row = cur.fetchone()
    return row[0] if row else None


def query_facts_df(
    conn: sqlite3.Connection,
    cik: int,
    statement: str | None = None,
    period: str = "annual",
) -> pd.DataFrame:
    sql = "SELECT * FROM facts WHERE cik = ?"
    params: list[Any] = [cik]

    if statement:
        sql += " AND statement = ?"
        params.append(statement)

    if period == "annual":
        sql += " AND form = '10-K'"
    elif period == "quarterly":
        sql += " AND form = '10-Q'"

    sql += " ORDER BY period_end DESC, canonical_name"
    return pd.read_sql_query(sql, conn, params=params)


def get_db_stats(conn: sqlite3.Connection) -> dict[str, Any]:
    stats: dict[str, Any] = {}
    cur = conn.execute("SELECT COUNT(*) FROM companies")
    stats["companies"] = cur.fetchone()[0]
    cur = conn.execute("SELECT COUNT(*) FROM facts")
    stats["facts"] = cur.fetchone()[0]
    cur = conn.execute("SELECT COUNT(*) FROM ticker_map")
    stats["tickers"] = cur.fetchone()[0]
    cur = conn.execute("SELECT COUNT(DISTINCT statement) FROM facts")
    stats["statements"] = cur.fetchone()[0]
    return stats
