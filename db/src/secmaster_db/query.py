"""Query API for Security Master data."""

from __future__ import annotations

import sqlite3

import pandas as pd

from .models import SecurityRow


class SecMasterQuery:
    """High-level query interface for security master data."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> SecMasterQuery:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def get_security(self, ticker: str) -> SecurityRow | None:
        cur = self._conn.execute(
            "SELECT * FROM securities WHERE ticker = ?", (ticker.upper(),)
        )
        row = cur.fetchone()
        if row is None:
            return None
        cols = [desc[0] for desc in cur.description]
        return SecurityRow(**dict(zip(cols, row)))

    def list_all(self) -> pd.DataFrame:
        return pd.read_sql_query(
            "SELECT ticker, name, sector, industry, country, style_box FROM securities ORDER BY ticker",
            self._conn,
        )

    def search(
        self,
        sector: str | None = None,
        industry: str | None = None,
        country: str | None = None,
        style_box: str | None = None,
    ) -> pd.DataFrame:
        conditions: list[str] = []
        params: list[str] = []
        if sector:
            conditions.append("sector = ?")
            params.append(sector)
        if industry:
            conditions.append("industry = ?")
            params.append(industry)
        if country:
            conditions.append("country = ?")
            params.append(country)
        if style_box:
            conditions.append("style_box = ?")
            params.append(style_box)

        where = " AND ".join(conditions) if conditions else "1=1"
        sql = f"SELECT ticker, name, sector, industry, country, style_box, market_cap FROM securities WHERE {where} ORDER BY ticker"
        return pd.read_sql_query(sql, self._conn, params=params)

    def list_by_sector(self) -> pd.DataFrame:
        return pd.read_sql_query(
            """SELECT sector, COUNT(*) as count,
                      ROUND(SUM(market_cap)/1e9, 2) as total_market_cap_b
               FROM securities WHERE sector != ''
               GROUP BY sector ORDER BY count DESC""",
            self._conn,
        )

    def list_by_style_box(self) -> pd.DataFrame:
        return pd.read_sql_query(
            """SELECT style_box, COUNT(*) as count,
                      ROUND(SUM(market_cap)/1e9, 2) as total_market_cap_b
               FROM securities WHERE style_box != ''
               GROUP BY style_box ORDER BY count DESC""",
            self._conn,
        )
