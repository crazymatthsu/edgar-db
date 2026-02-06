"""Smoke tests for the CLI using Click's CliRunner."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from edgar_db.cli import cli
from edgar_db.db import connect_db, upsert_company, upsert_facts, upsert_ticker_map
from edgar_db.models import Company, FactRow

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _setup_test_db(db_path: Path) -> None:
    """Populate a test DB with sample data."""
    conn = connect_db(db_path)
    upsert_ticker_map(conn, {"AAPL": 320193})
    upsert_company(conn, Company(cik=320193, name="Apple Inc.", ticker="AAPL"))
    upsert_facts(conn, [
        FactRow(
            cik=320193, tag="Revenues", canonical_name="revenue",
            statement="income", value=383285000000, unit="USD",
            period_end="2023-09-30", fiscal_year=2023, fiscal_period="FY",
            form="10-K", filed="2023-11-03", accession="0000320193-23-000106",
        ),
        FactRow(
            cik=320193, tag="NetIncomeLoss", canonical_name="net_income",
            statement="income", value=96995000000, unit="USD",
            period_end="2023-09-30", fiscal_year=2023, fiscal_period="FY",
            form="10-K", filed="2023-11-03", accession="0000320193-23-000106",
        ),
    ])
    conn.close()


class TestInfoCommand:
    def test_info_shows_stats(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.db"
        _setup_test_db(db_path)

        runner = CliRunner()
        with patch("edgar_db.cli._get_config") as mock_config:
            mock_config.return_value = MagicMock(db_path=db_path)
            result = runner.invoke(cli, ["info"])
            assert result.exit_code == 0
            assert "1" in result.output  # At least 1 company


class TestShowCommand:
    def test_show_table(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.db"
        _setup_test_db(db_path)

        runner = CliRunner()
        with patch("edgar_db.cli._get_config") as mock_config:
            mock_config.return_value = MagicMock(db_path=db_path)
            result = runner.invoke(cli, ["show", "AAPL", "--statement", "income"])
            assert result.exit_code == 0

    def test_show_csv(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.db"
        _setup_test_db(db_path)

        runner = CliRunner()
        with patch("edgar_db.cli._get_config") as mock_config:
            mock_config.return_value = MagicMock(db_path=db_path)
            result = runner.invoke(cli, ["show", "AAPL", "--statement", "income", "--format", "csv"])
            assert result.exit_code == 0
            assert "revenue" in result.output


class TestDownloadCommand:
    def test_requires_ticker_or_sp500(self) -> None:
        runner = CliRunner()
        with patch("edgar_db.cli._get_config") as mock_config:
            mock_config.return_value = MagicMock(
                db_path=Path("/tmp/test.db"),
                user_agent="test",
                rate_limit=10.0,
                timeout=30.0,
                max_retries=3,
            )
            mock_config.return_value.ensure_db_dir = MagicMock()
            result = runner.invoke(cli, ["download"])
            assert result.exit_code != 0 or "Error" in result.output
