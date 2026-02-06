"""EDGAR Financial Database — SEC EDGAR data in SQLite for AI and quant analysis."""

from __future__ import annotations

from pathlib import Path

from .db import connect_db
from .query import EdgarQuery


def connect(db_path: str | Path | None = None) -> EdgarQuery:
    """Connect to the EDGAR database and return a query interface.

    Args:
        db_path: Path to SQLite database. Defaults to ~/.edgar-db/edgar.db

    Returns:
        EdgarQuery instance with methods like get_income_statement(), etc.
    """
    if db_path is None:
        db_path = Path.home() / ".edgar-db" / "edgar.db"
    else:
        db_path = Path(db_path)

    conn = connect_db(db_path)
    return EdgarQuery(conn)


__all__ = ["connect", "EdgarQuery"]
