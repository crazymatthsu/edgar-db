"""Dependency injection for FastAPI routes."""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Generator

from edgar_db.config import Config
from edgar_db.db import connect_db
from edgar_db.query import EdgarQuery

_conn: sqlite3.Connection | None = None
_db_path: Path | None = None


def get_db_path() -> Path:
    global _db_path
    if _db_path is not None:
        return _db_path
    return Path(os.environ.get("EDGAR_DB_PATH", Path.home() / ".edgar-db" / "edgar.db"))


def set_db_path(path: Path) -> None:
    global _db_path
    _db_path = path


def get_conn() -> sqlite3.Connection:
    global _conn
    if _conn is None:
        _conn = connect_db(get_db_path())
    return _conn


def close_conn() -> None:
    global _conn
    if _conn is not None:
        _conn.close()
        _conn = None


def get_query() -> EdgarQuery:
    return EdgarQuery(get_conn())


def get_config() -> Config:
    return Config(db_path=get_db_path())
