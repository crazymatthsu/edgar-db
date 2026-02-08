from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from secmaster_db.db import connect_db
from secmaster_db.models import SecurityRow


@pytest.fixture
def tmp_db(tmp_path: Path) -> sqlite3.Connection:
    db_path = tmp_path / "test.db"
    return connect_db(db_path)


def _make_security(**overrides: object) -> SecurityRow:
    defaults = dict(
        ticker="AAPL",
        name="Apple Inc.",
        isin="US0378331005",
        cusip="",
        sedol="",
        primary_ric="",
        bloomberg_code="",
        figi="BBG000B9XRY4",
        share_class_figi="BBG001S5N8V8",
        shares_outstanding=15_000_000_000,
        country="United States",
        exchange_mic="XNAS",
        exchange_currency="USD",
        sector="Technology",
        industry="Consumer Electronics",
        market_cap=3_000_000_000_000.0,
        style_box="large_cap",
        last_updated="2024-01-01T00:00:00+00:00",
    )
    defaults.update(overrides)
    return SecurityRow(**defaults)
