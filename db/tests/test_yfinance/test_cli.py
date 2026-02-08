from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from yfinance_db.cli import cli


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


def test_info_command(tmp_path: Path, runner: CliRunner) -> None:
    db_path = tmp_path / "test.db"
    with patch("yfinance_db.cli._get_config") as mock_get_config:
        mock_config = MagicMock()
        mock_config.db_path = db_path
        mock_get_config.return_value = mock_config

        from yfinance_db.db import connect_db
        conn = connect_db(db_path)
        conn.close()

        result = runner.invoke(cli, ["info"])
        assert result.exit_code == 0
        assert "Yahoo Finance Database Info" in result.output


def test_download_no_ticker(runner: CliRunner) -> None:
    result = runner.invoke(cli, ["download"])
    assert result.exit_code != 0
    assert "Provide --ticker or --sp500" in result.output


def test_show_unknown_ticker(tmp_path: Path, runner: CliRunner) -> None:
    db_path = tmp_path / "test.db"
    with patch("yfinance_db.cli._get_config") as mock_get_config:
        mock_config = MagicMock()
        mock_config.db_path = db_path
        mock_get_config.return_value = mock_config

        from yfinance_db.db import connect_db
        conn = connect_db(db_path)
        conn.close()

        result = runner.invoke(cli, ["show", "NONEXIST", "--data", "prices"])
        assert result.exit_code == 0
        assert "no" in result.output.lower()


def test_version(runner: CliRunner) -> None:
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert "0.1.0" in result.output


def test_download_sp500(tmp_path: Path, runner: CliRunner) -> None:
    db_path = tmp_path / "test.db"

    from yfinance_db.db import connect_db
    conn = connect_db(db_path)
    conn.close()

    with patch("yfinance_db.cli._get_config") as mock_get_config, \
         patch("edgar_db.sp500.get_sp500_tickers", return_value=["AAPL", "MSFT"]), \
         patch("yfinance_db.downloader.download_batch") as mock_batch, \
         patch("yfinance_db.client.YFinanceClient"):
        mock_config = MagicMock()
        mock_config.db_path = db_path
        mock_get_config.return_value = mock_config
        mock_batch.return_value = {"AAPL": {"prices": 100}, "MSFT": {"prices": 50}}

        result = runner.invoke(cli, ["download", "--sp500"])
        assert result.exit_code == 0
        assert "2 succeeded" in result.output


def test_download_single_ticker(tmp_path: Path, runner: CliRunner) -> None:
    db_path = tmp_path / "test.db"

    from yfinance_db.db import connect_db
    conn = connect_db(db_path)
    conn.close()

    with patch("yfinance_db.cli._get_config") as mock_get_config, \
         patch("yfinance_db.downloader.download_company") as mock_download, \
         patch("yfinance_db.client.YFinanceClient"):
        mock_config = MagicMock()
        mock_config.db_path = db_path
        mock_get_config.return_value = mock_config
        mock_download.return_value = {"prices": 100}

        result = runner.invoke(cli, ["download", "-t", "AAPL"])
        assert result.exit_code == 0
        assert "100 records" in result.output
