"""Security Master Database — security reference data in SQLite for AI and quantitative analysis."""

from __future__ import annotations

from pathlib import Path

from .db import connect_db
from .query import SecMasterQuery


def connect(db_path: str | Path | None = None) -> SecMasterQuery:
    """Connect to the Security Master database and return a query interface.

    Args:
        db_path: Path to SQLite database. Defaults to ~/.secmaster-db/secmaster.db

    Returns:
        SecMasterQuery instance.
    """
    if db_path is None:
        db_path = Path.home() / ".secmaster-db" / "secmaster.db"
    else:
        db_path = Path(db_path)

    conn = connect_db(db_path)
    return SecMasterQuery(conn)


__all__ = ["connect", "SecMasterQuery"]
