from __future__ import annotations

import time
from unittest.mock import MagicMock, patch

import pytest

from secmaster_db.config import Config


@pytest.fixture
def yf_client():
    mock_yf = MagicMock()
    with patch("secmaster_db.client._import_yf", return_value=mock_yf):
        from secmaster_db.client import YFinanceClient
        config = Config(rate_limit=100.0, max_retries=2)
        c = YFinanceClient(config)
    return c


@pytest.fixture
def figi_client():
    from secmaster_db.client import OpenFIGIClient
    config = Config(openfigi_api_key="")
    return OpenFIGIClient(config)


def test_yf_get_info(yf_client) -> None:
    mock_ticker = MagicMock()
    mock_ticker.info = {
        "longName": "Apple Inc.",
        "regularMarketPrice": 185.0,
        "marketCap": 3_000_000_000_000,
        "isin": "US0378331005",
        "sector": "Technology",
    }
    yf_client._yf.Ticker.return_value = mock_ticker

    info = yf_client.get_info("AAPL")
    assert info["longName"] == "Apple Inc."
    assert info["isin"] == "US0378331005"
    yf_client._yf.Ticker.assert_called_with("AAPL")


def test_yf_get_info_retry(yf_client) -> None:
    call_count = 0

    def _make_ticker(symbol):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise ConnectionError("timeout")
        mock_t = MagicMock()
        mock_t.info = {"regularMarketPrice": 185.0, "longName": "Apple"}
        return mock_t

    yf_client._yf.Ticker.side_effect = _make_ticker
    info = yf_client.get_info("AAPL")
    assert info["longName"] == "Apple"
    assert call_count == 2


def test_yf_throttle(yf_client) -> None:
    yf_client._config.rate_limit = 10.0
    yf_client._min_interval = 0.1

    start = time.monotonic()
    yf_client._throttle()
    yf_client._throttle()
    elapsed = time.monotonic() - start
    assert elapsed >= 0.09


def test_figi_fetch_success(figi_client) -> None:
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [
        {
            "data": [
                {
                    "figi": "BBG000B9XRY4",
                    "compositeFIGI": "BBG000B9Y5X2",
                    "shareClassFIGI": "BBG001S5N8V8",
                    "micCode": "XNAS",
                    "securityType": "Common Stock",
                }
            ]
        }
    ]
    mock_response.raise_for_status = MagicMock()

    with patch("secmaster_db.client.httpx.post", return_value=mock_response):
        result = figi_client.fetch_figi("AAPL")

    assert result is not None
    assert result["figi"] == "BBG000B9XRY4"
    assert result["shareClassFIGI"] == "BBG001S5N8V8"
    assert result["micCode"] == "XNAS"


def test_figi_fetch_error_returns_none(figi_client) -> None:
    with patch("secmaster_db.client.httpx.post", side_effect=Exception("network error")):
        result = figi_client.fetch_figi("AAPL")

    assert result is None


def test_figi_fetch_empty_response(figi_client) -> None:
    mock_response = MagicMock()
    mock_response.json.return_value = [{"warning": "No match found"}]
    mock_response.raise_for_status = MagicMock()

    with patch("secmaster_db.client.httpx.post", return_value=mock_response):
        result = figi_client.fetch_figi("UNKNOWN")

    assert result is None
