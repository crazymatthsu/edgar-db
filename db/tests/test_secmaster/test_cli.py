from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from secmaster_db.cli import cli


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


def test_info_command(tmp_path: Path, runner: CliRunner) -> None:
    db_path = tmp_path / "test.db"
    with patch("secmaster_db.cli._get_config") as mock_get_config:
        mock_config = MagicMock()
        mock_config.db_path = db_path
        mock_get_config.return_value = mock_config

        from secmaster_db.db import connect_db
        conn = connect_db(db_path)
        conn.close()

        result = runner.invoke(cli, ["info"])
        assert result.exit_code == 0
        assert "Security Master Database Info" in result.output


def test_download_no_ticker(runner: CliRunner) -> None:
    result = runner.invoke(cli, ["download"])
    assert result.exit_code != 0
    assert "Provide --ticker or --sp500" in result.output


def test_show_unknown_ticker(tmp_path: Path, runner: CliRunner) -> None:
    db_path = tmp_path / "test.db"
    with patch("secmaster_db.cli._get_config") as mock_get_config:
        mock_config = MagicMock()
        mock_config.db_path = db_path
        mock_get_config.return_value = mock_config

        from secmaster_db.db import connect_db
        conn = connect_db(db_path)
        conn.close()

        result = runner.invoke(cli, ["show", "NONEXIST"])
        assert result.exit_code == 0
        assert "no data" in result.output.lower()


def test_version(runner: CliRunner) -> None:
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert "0.1.0" in result.output


def test_download_single_ticker(tmp_path: Path, runner: CliRunner) -> None:
    db_path = tmp_path / "test.db"

    from secmaster_db.db import connect_db
    conn = connect_db(db_path)
    conn.close()

    with patch("secmaster_db.cli._get_config") as mock_get_config, \
         patch("secmaster_db.downloader.download_security") as mock_download, \
         patch("secmaster_db.client.YFinanceClient"), \
         patch("secmaster_db.client.OpenFIGIClient"):
        mock_config = MagicMock()
        mock_config.db_path = db_path
        mock_get_config.return_value = mock_config
        mock_download.return_value = True

        result = runner.invoke(cli, ["download", "-t", "AAPL"])
        assert result.exit_code == 0
        assert "done" in result.output.lower()


def test_download_already_fresh(tmp_path: Path, runner: CliRunner) -> None:
    db_path = tmp_path / "test.db"

    from secmaster_db.db import connect_db
    conn = connect_db(db_path)
    conn.close()

    with patch("secmaster_db.cli._get_config") as mock_get_config, \
         patch("secmaster_db.downloader.download_security") as mock_download, \
         patch("secmaster_db.client.YFinanceClient"), \
         patch("secmaster_db.client.OpenFIGIClient"):
        mock_config = MagicMock()
        mock_config.db_path = db_path
        mock_get_config.return_value = mock_config
        mock_download.return_value = False

        result = runner.invoke(cli, ["download", "-t", "AAPL"])
        assert result.exit_code == 0
        assert "already up to date" in result.output.lower()


def test_download_sp500(tmp_path: Path, runner: CliRunner) -> None:
    db_path = tmp_path / "test.db"

    from secmaster_db.db import connect_db
    conn = connect_db(db_path)
    conn.close()

    with patch("secmaster_db.cli._get_config") as mock_get_config, \
         patch("edgar_db.sp500.get_sp500_tickers", return_value=["AAPL", "MSFT"]), \
         patch("secmaster_db.downloader.download_batch") as mock_batch, \
         patch("secmaster_db.client.YFinanceClient"), \
         patch("secmaster_db.client.OpenFIGIClient"):
        mock_config = MagicMock()
        mock_config.db_path = db_path
        mock_get_config.return_value = mock_config
        mock_batch.return_value = {"AAPL": True, "MSFT": True}

        result = runner.invoke(cli, ["download", "--sp500"])
        assert result.exit_code == 0
        assert "2 succeeded" in result.output


def test_search_command(tmp_path: Path, runner: CliRunner) -> None:
    db_path = tmp_path / "test.db"

    from secmaster_db.db import connect_db, upsert_security
    from secmaster_db.models import SecurityRow
    conn = connect_db(db_path)
    upsert_security(conn, SecurityRow(
        ticker="AAPL", name="Apple Inc.", sector="Technology",
        market_cap=3e12, style_box="large_cap",
    ))
    conn.close()

    with patch("secmaster_db.cli._get_config") as mock_get_config:
        mock_config = MagicMock()
        mock_config.db_path = db_path
        mock_get_config.return_value = mock_config

        result = runner.invoke(cli, ["search", "--sector", "Technology"])
        assert result.exit_code == 0
        assert "AAPL" in result.output


def test_search_no_results(tmp_path: Path, runner: CliRunner) -> None:
    db_path = tmp_path / "test.db"

    from secmaster_db.db import connect_db
    conn = connect_db(db_path)
    conn.close()

    with patch("secmaster_db.cli._get_config") as mock_get_config:
        mock_config = MagicMock()
        mock_config.db_path = db_path
        mock_get_config.return_value = mock_config

        result = runner.invoke(cli, ["search", "--sector", "Energy"])
        assert result.exit_code == 0
        assert "no securities" in result.output.lower()
