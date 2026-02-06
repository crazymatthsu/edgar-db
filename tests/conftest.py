from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from edgar_db.db import connect_db

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_facts_json() -> dict:
    with open(FIXTURES_DIR / "company_facts_sample.json") as f:
        return json.load(f)


@pytest.fixture
def sample_tickers_json() -> dict:
    with open(FIXTURES_DIR / "company_tickers_sample.json") as f:
        return json.load(f)


@pytest.fixture
def tmp_db(tmp_path: Path) -> sqlite3.Connection:
    db_path = tmp_path / "test.db"
    return connect_db(db_path)
