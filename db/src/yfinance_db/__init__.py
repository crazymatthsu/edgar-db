"""Yahoo Finance Database — market data in SQLite for AI and quantitative analysis."""

from __future__ import annotations

from pathlib import Path

from .db import connect_db
from .query import YFinanceQuery


def connect(db_path: str | Path | None = None) -> YFinanceQuery:
    """Connect to the Yahoo Finance database and return a query interface.

    Args:
        db_path: Path to SQLite database. Defaults to ~/.yfinance-db/yfinance.db

    Returns:
        YFinanceQuery instance.
    """
    if db_path is None:
        db_path = Path.home() / ".yfinance-db" / "yfinance.db"
    else:
        db_path = Path(db_path)

    conn = connect_db(db_path)
    return YFinanceQuery(conn)


__all__ = ["connect", "YFinanceQuery"]
