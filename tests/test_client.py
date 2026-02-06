"""Tests for the HTTP client with mocked responses."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import httpx
import pytest
import respx

from edgar_db.client import BASE_URL, EdgarClient
from edgar_db.config import Config

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def config() -> Config:
    return Config(user_agent="TestApp test@example.com", rate_limit=100.0)


@pytest.fixture
def client(config: Config) -> EdgarClient:
    c = EdgarClient(config)
    yield c
    c.close()


class TestGetCompanyTickers:
    @respx.mock
    def test_fetches_tickers(self, client: EdgarClient, sample_tickers_json: dict) -> None:
        respx.get(f"{BASE_URL}/files/company_tickers.json").mock(
            return_value=httpx.Response(200, json=sample_tickers_json)
        )
        result = client.get_company_tickers()
        assert "0" in result
        assert result["0"]["ticker"] == "AAPL"

    @respx.mock
    def test_retries_on_500(self, client: EdgarClient, sample_tickers_json: dict) -> None:
        route = respx.get(f"{BASE_URL}/files/company_tickers.json")
        route.side_effect = [
            httpx.Response(500),
            httpx.Response(200, json=sample_tickers_json),
        ]
        result = client.get_company_tickers()
        assert result["0"]["ticker"] == "AAPL"

    @respx.mock
    def test_raises_on_persistent_failure(self, client: EdgarClient) -> None:
        respx.get(f"{BASE_URL}/files/company_tickers.json").mock(
            return_value=httpx.Response(500)
        )
        with pytest.raises(httpx.HTTPStatusError):
            client.get_company_tickers()


class TestGetCompanyFacts:
    @respx.mock
    def test_fetches_facts(self, client: EdgarClient, sample_facts_json: dict) -> None:
        cik = 320193
        padded = str(cik).zfill(10)
        respx.get(f"{BASE_URL}/api/xbrl/companyfacts/CIK{padded}.json").mock(
            return_value=httpx.Response(200, json=sample_facts_json)
        )
        result = client.get_company_facts(cik)
        assert result["entityName"] == "Apple Inc."

    @respx.mock
    def test_404_raises(self, client: EdgarClient) -> None:
        cik = 999999999
        padded = str(cik).zfill(10)
        respx.get(f"{BASE_URL}/api/xbrl/companyfacts/CIK{padded}.json").mock(
            return_value=httpx.Response(404)
        )
        with pytest.raises(httpx.HTTPStatusError):
            client.get_company_facts(cik)


class TestRateLimiting:
    def test_throttle_spacing(self, config: Config) -> None:
        """Rate limiter should enforce minimum interval between requests."""
        import time
        config.rate_limit = 5.0  # 5 req/sec → 0.2s interval
        c = EdgarClient(config)
        c._last_request_time = time.monotonic()
        start = time.monotonic()
        c._throttle()
        elapsed = time.monotonic() - start
        assert elapsed >= 0.15  # Allow some tolerance
        c.close()


class TestPadCik:
    def test_padding(self) -> None:
        assert EdgarClient.pad_cik(320193) == "0000320193"
        assert EdgarClient.pad_cik(1) == "0000000001"
