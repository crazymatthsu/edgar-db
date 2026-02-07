"""DataFrame query API for Yahoo Finance data."""

from __future__ import annotations

import sqlite3

import pandas as pd


class YFinanceQuery:
    """High-level query interface returning pandas DataFrames."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> YFinanceQuery:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def get_prices(
        self,
        ticker: str,
        start: str | None = None,
        end: str | None = None,
        interval: str = "1d",
    ) -> pd.DataFrame:
        sql = "SELECT date, open, high, low, close, volume FROM prices WHERE ticker = ? AND interval = ?"
        params: list[object] = [ticker.upper(), interval]
        if start:
            sql += " AND date >= ?"
            params.append(start)
        if end:
            sql += " AND date <= ?"
            params.append(end)
        sql += " ORDER BY date"
        return pd.read_sql_query(sql, self._conn, params=params)

    def get_company_info(self, ticker: str) -> pd.Series:
        cur = self._conn.execute(
            "SELECT * FROM companies WHERE ticker = ?", (ticker.upper(),)
        )
        row = cur.fetchone()
        if row is None:
            raise ValueError(f"Unknown ticker: {ticker}. Try downloading first.")
        cols = [desc[0] for desc in cur.description]
        return pd.Series(dict(zip(cols, row)))

    def get_stats(self, ticker: str) -> pd.DataFrame:
        return pd.read_sql_query(
            "SELECT * FROM company_stats WHERE ticker = ? ORDER BY fetched_date DESC",
            self._conn,
            params=[ticker.upper()],
        )

    def _get_statement(
        self, ticker: str, statement: str, period: str = "annual"
    ) -> pd.DataFrame:
        df = pd.read_sql_query(
            """SELECT period_end, metric, value FROM financials
               WHERE ticker = ? AND statement = ? AND period_type = ?
               ORDER BY period_end DESC""",
            self._conn,
            params=[ticker.upper(), statement, period],
        )
        if df.empty:
            return pd.DataFrame()
        pivot = df.pivot_table(
            index="period_end", columns="metric", values="value", aggfunc="first"
        )
        pivot = pivot.reset_index().sort_values("period_end", ascending=False)
        return pivot.reset_index(drop=True)

    def get_income_statement(
        self, ticker: str, period: str = "annual"
    ) -> pd.DataFrame:
        return self._get_statement(ticker, "income", period)

    def get_balance_sheet(
        self, ticker: str, period: str = "annual"
    ) -> pd.DataFrame:
        return self._get_statement(ticker, "balance", period)

    def get_cash_flow(
        self, ticker: str, period: str = "annual"
    ) -> pd.DataFrame:
        return self._get_statement(ticker, "cashflow", period)

    def get_dividends(self, ticker: str) -> pd.DataFrame:
        return pd.read_sql_query(
            "SELECT date, amount FROM dividends WHERE ticker = ? ORDER BY date DESC",
            self._conn,
            params=[ticker.upper()],
        )

    def get_splits(self, ticker: str) -> pd.DataFrame:
        return pd.read_sql_query(
            "SELECT date, ratio FROM splits WHERE ticker = ? ORDER BY date DESC",
            self._conn,
            params=[ticker.upper()],
        )

    def get_metric(
        self, ticker: str, metric: str, period: str = "annual"
    ) -> pd.DataFrame:
        return pd.read_sql_query(
            """SELECT period_end, value FROM financials
               WHERE ticker = ? AND metric = ? AND period_type = ?
               ORDER BY period_end DESC""",
            self._conn,
            params=[ticker.upper(), metric, period],
        )

    def compare(
        self, tickers: list[str], metric: str, period: str = "annual"
    ) -> pd.DataFrame:
        frames: dict[str, pd.Series] = {}
        for ticker in tickers:
            df = self.get_metric(ticker, metric, period)
            if not df.empty:
                series = df.set_index("period_end")["value"]
                series.name = ticker.upper()
                frames[ticker.upper()] = series
        if not frames:
            return pd.DataFrame()
        result = pd.DataFrame(frames)
        result.index.name = "period_end"
        return result.sort_index(ascending=False)

    def compare_prices(
        self,
        tickers: list[str],
        start: str | None = None,
        end: str | None = None,
    ) -> pd.DataFrame:
        frames: dict[str, pd.Series] = {}
        for ticker in tickers:
            df = self.get_prices(ticker, start=start, end=end)
            if not df.empty:
                series = df.set_index("date")["close"]
                series.name = ticker.upper()
                frames[ticker.upper()] = series
        if not frames:
            return pd.DataFrame()
        result = pd.DataFrame(frames)
        result.index.name = "date"
        return result.sort_index()
