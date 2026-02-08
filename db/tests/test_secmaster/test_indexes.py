from __future__ import annotations

from unittest.mock import patch

import pytest

from secmaster_db.indexes import (
    _fetch_wikipedia_tickers,
    get_dji_tickers,
    get_index_tickers,
    get_ndx_tickers,
    get_spx_tickers,
    list_supported_indexes,
)

_SAMPLE_HTML = """
<html><body>
<table class="wikitable">
<tr><th>Symbol</th><th>Name</th></tr>
<tr><td>AAPL</td><td>Apple Inc.</td></tr>
<tr><td>MSFT</td><td>Microsoft Corp.</td></tr>
<tr><td>BRK.B</td><td>Berkshire Hathaway</td></tr>
</table>
</body></html>
"""

_SAMPLE_HTML_TICKER_COL = """
<html><body>
<table class="wikitable">
<tr><th>Ticker</th><th>Company</th></tr>
<tr><td>AMZN</td><td>Amazon</td></tr>
<tr><td>GOOG</td><td>Alphabet</td></tr>
</table>
</body></html>
"""


class _FakeResponse:
    def __init__(self, text: str) -> None:
        self.text = text

    def raise_for_status(self) -> None:
        pass


def test_fetch_wikipedia_tickers_symbol_column() -> None:
    with patch("secmaster_db.indexes.httpx.get", return_value=_FakeResponse(_SAMPLE_HTML)):
        tickers = _fetch_wikipedia_tickers("http://example.com", ["Symbol", "Ticker"])
    assert tickers == ["AAPL", "MSFT", "BRK-B"]


def test_fetch_wikipedia_tickers_ticker_column() -> None:
    with patch("secmaster_db.indexes.httpx.get", return_value=_FakeResponse(_SAMPLE_HTML_TICKER_COL)):
        tickers = _fetch_wikipedia_tickers("http://example.com", ["Ticker"])
    assert tickers == ["AMZN", "GOOG"]


def test_fetch_wikipedia_tickers_no_matching_column() -> None:
    with patch("secmaster_db.indexes.httpx.get", return_value=_FakeResponse(_SAMPLE_HTML)):
        with pytest.raises(ValueError, match="Could not find ticker column"):
            _fetch_wikipedia_tickers("http://example.com", ["NonExistent"])


def test_get_spx_tickers() -> None:
    with patch("secmaster_db.indexes.httpx.get", return_value=_FakeResponse(_SAMPLE_HTML)):
        tickers = get_spx_tickers()
    assert "AAPL" in tickers
    assert "BRK-B" in tickers


def test_get_dji_tickers() -> None:
    with patch("secmaster_db.indexes.httpx.get", return_value=_FakeResponse(_SAMPLE_HTML)):
        tickers = get_dji_tickers()
    assert "AAPL" in tickers


def test_get_ndx_tickers() -> None:
    with patch("secmaster_db.indexes.httpx.get", return_value=_FakeResponse(_SAMPLE_HTML_TICKER_COL)):
        tickers = get_ndx_tickers()
    assert "AMZN" in tickers


def test_get_index_tickers_dispatch() -> None:
    with patch("secmaster_db.indexes.httpx.get", return_value=_FakeResponse(_SAMPLE_HTML)):
        result = get_index_tickers("SPX")
    assert "AAPL" in result


def test_get_index_tickers_case_insensitive() -> None:
    with patch("secmaster_db.indexes.httpx.get", return_value=_FakeResponse(_SAMPLE_HTML)):
        result = get_index_tickers("spx")
    assert "AAPL" in result


def test_get_index_tickers_unknown() -> None:
    with pytest.raises(ValueError, match="Unknown index"):
        get_index_tickers("INVALID")


def test_list_supported_indexes() -> None:
    result = list_supported_indexes()
    assert result == ["DJI", "NDX", "SPX"]
