"""DataFrame query API — pivots raw facts into statement-shaped DataFrames."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd

from .db import connect_db, query_facts_df, resolve_cik
from .xbrl_tags import STATEMENT_COLUMNS


class EdgarQuery:
    """High-level query interface returning pandas DataFrames."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> EdgarQuery:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def _resolve_cik(self, ticker: str) -> int:
        cik = resolve_cik(self._conn, ticker.upper())
        if cik is None:
            raise ValueError(f"Unknown ticker: {ticker}. Try downloading first.")
        return cik

    def _pivot_statement(
        self, ticker: str, statement: str, period: str = "annual"
    ) -> pd.DataFrame:
        """Pivot raw facts into a statement-shaped DataFrame.

        Rows = periods (fiscal_year + fiscal_period), Columns = canonical metrics.
        """
        cik = self._resolve_cik(ticker)
        df = query_facts_df(self._conn, cik, statement=statement, period=period)

        if df.empty:
            return pd.DataFrame()

        # Pivot: rows are periods, columns are metrics
        pivot = df.pivot_table(
            index=["fiscal_year", "fiscal_period", "period_end"],
            columns="canonical_name",
            values="value",
            aggfunc="first",
        )

        pivot = pivot.reset_index()
        pivot = pivot.sort_values("period_end", ascending=False)

        # Reorder columns to match canonical order
        expected_cols = STATEMENT_COLUMNS.get(statement, [])
        index_cols = ["fiscal_year", "fiscal_period", "period_end"]
        ordered = index_cols + [c for c in expected_cols if c in pivot.columns]
        # Include any extra columns not in the expected list
        extra = [c for c in pivot.columns if c not in ordered]
        pivot = pivot[ordered + extra]

        return pivot.reset_index(drop=True)

    def get_income_statement(
        self, ticker: str, period: str = "annual"
    ) -> pd.DataFrame:
        return self._pivot_statement(ticker, "income", period)

    def get_balance_sheet(
        self, ticker: str, period: str = "annual"
    ) -> pd.DataFrame:
        return self._pivot_statement(ticker, "balance", period)

    def get_cash_flow(
        self, ticker: str, period: str = "annual"
    ) -> pd.DataFrame:
        df = self._pivot_statement(ticker, "cashflow", period)
        if not df.empty and "operating_cash_flow" in df.columns and "capital_expenditure" in df.columns:
            df["free_cash_flow"] = df["operating_cash_flow"] - df["capital_expenditure"]
        return df

    def get_metric(
        self, ticker: str, metric: str, period: str = "annual"
    ) -> pd.DataFrame:
        """Get a single metric's time series."""
        cik = self._resolve_cik(ticker)

        form = "10-K" if period == "annual" else "10-Q"
        df = pd.read_sql_query(
            """SELECT fiscal_year, fiscal_period, period_end, value
               FROM facts
               WHERE cik = ? AND canonical_name = ? AND form = ?
               ORDER BY period_end DESC""",
            self._conn,
            params=[cik, metric, form],
        )
        return df

    def compare(
        self, tickers: list[str], metric: str, period: str = "annual"
    ) -> pd.DataFrame:
        """Compare a metric across multiple tickers. Returns pivoted DataFrame."""
        frames = {}
        for ticker in tickers:
            try:
                df = self.get_metric(ticker, metric, period)
            except ValueError:
                continue
            if not df.empty:
                series = df.set_index("period_end")["value"]
                series.name = ticker.upper()
                frames[ticker.upper()] = series

        if not frames:
            return pd.DataFrame()

        result = pd.DataFrame(frames)
        result.index.name = "period_end"
        result = result.sort_index(ascending=False)
        return result
