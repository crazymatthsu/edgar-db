from __future__ import annotations

import time
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from yfinance_db.config import Config


@pytest.fixture
def client():
    mock_yf = MagicMock()
    with patch("yfinance_db.client._import_yf", return_value=mock_yf):
        from yfinance_db.client import YFinanceClient
        config = Config(rate_limit=100.0, max_retries=2)
        c = YFinanceClient(config)
    return c


def test_throttle(client) -> None:
    """Rate limiting should space out requests."""
    client._config.rate_limit = 10.0
    client._min_interval = 0.1

    start = time.monotonic()
    client._throttle()
    client._throttle()
    elapsed = time.monotonic() - start
    assert elapsed >= 0.09


def test_get_info(client) -> None:
    mock_ticker = MagicMock()
    mock_ticker.info = {
        "longName": "Apple Inc.",
        "regularMarketPrice": 185.0,
        "marketCap": 3_000_000_000_000,
    }
    client._yf.Ticker.return_value = mock_ticker

    info = client.get_info("AAPL")
    assert info["longName"] == "Apple Inc."
    client._yf.Ticker.assert_called_with("AAPL")


def test_get_info_retry_on_error(client) -> None:
    call_count = 0

    def _make_ticker(symbol):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise ConnectionError("timeout")
        mock_t = MagicMock()
        mock_t.info = {"regularMarketPrice": 185.0, "longName": "Apple"}
        return mock_t

    client._yf.Ticker.side_effect = _make_ticker
    info = client.get_info("AAPL")
    assert info["longName"] == "Apple"
    assert call_count == 2


def test_get_history(client) -> None:
    mock_ticker = MagicMock()
    dates = pd.to_datetime(["2024-01-02"])
    mock_ticker.history.return_value = pd.DataFrame(
        {"Open": [185.0], "High": [186.0], "Low": [184.0], "Close": [185.5], "Volume": [50_000_000]},
        index=dates,
    )
    client._yf.Ticker.return_value = mock_ticker

    df = client.get_history("AAPL", period="1y")
    assert len(df) == 1
    mock_ticker.history.assert_called_once_with(period="1y", interval="1d")


def test_get_history_empty_raises(client) -> None:
    mock_ticker = MagicMock()
    mock_ticker.history.return_value = pd.DataFrame()
    client._yf.Ticker.return_value = mock_ticker

    with pytest.raises(ValueError, match="No price history"):
        client.get_history("FAKE")


def test_get_financials(client) -> None:
    mock_ticker = MagicMock()
    dates = pd.to_datetime(["2023-09-30"])
    mock_ticker.income_stmt = pd.DataFrame(
        {dates[0]: [383_285e6]}, index=["Total Revenue"]
    )
    mock_ticker.quarterly_income_stmt = pd.DataFrame(
        {dates[0]: [90_000e6]}, index=["Total Revenue"]
    )
    client._yf.Ticker.return_value = mock_ticker

    df_annual = client.get_income_statement("AAPL", quarterly=False)
    assert not df_annual.empty

    df_quarterly = client.get_income_statement("AAPL", quarterly=True)
    assert not df_quarterly.empty


def test_get_dividends(client) -> None:
    mock_ticker = MagicMock()
    mock_ticker.dividends = pd.Series([0.24], index=pd.to_datetime(["2024-01-15"]))
    client._yf.Ticker.return_value = mock_ticker

    series = client.get_dividends("AAPL")
    assert len(series) == 1


def test_get_splits(client) -> None:
    mock_ticker = MagicMock()
    mock_ticker.splits = pd.Series([4.0], index=pd.to_datetime(["2020-08-31"]))
    client._yf.Ticker.return_value = mock_ticker

    series = client.get_splits("AAPL")
    assert len(series) == 1
