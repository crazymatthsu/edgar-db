"""Tests for the frontend API client with mocked HTTP responses."""

from __future__ import annotations

import httpx
import pytest
import respx

from ui.frontend.api_client import EdgarAPIClient


@pytest.fixture
def api_client() -> EdgarAPIClient:
    return EdgarAPIClient(base_url="http://test-api:8000")


class TestHealth:
    @respx.mock
    def test_health(self, api_client: EdgarAPIClient) -> None:
        respx.get("http://test-api:8000/api/health").mock(
            return_value=httpx.Response(200, json={"status": "ok", "db_path": "/tmp/test.db"})
        )
        result = api_client.health()
        assert result["status"] == "ok"

    @respx.mock
    def test_stats(self, api_client: EdgarAPIClient) -> None:
        respx.get("http://test-api:8000/api/stats").mock(
            return_value=httpx.Response(200, json={
                "companies": 5, "facts": 100, "tickers": 10, "statements": 3
            })
        )
        result = api_client.stats()
        assert result["companies"] == 5
        assert result["facts"] == 100


class TestDownload:
    @respx.mock
    def test_download(self, api_client: EdgarAPIClient) -> None:
        respx.post("http://test-api:8000/api/download/AAPL").mock(
            return_value=httpx.Response(200, json={
                "ticker": "AAPL", "status": "downloaded", "facts_count": 150
            })
        )
        result = api_client.download("AAPL")
        assert result["ticker"] == "AAPL"
        assert result["status"] == "downloaded"

    @respx.mock
    def test_download_404(self, api_client: EdgarAPIClient) -> None:
        respx.post("http://test-api:8000/api/download/ZZZZ").mock(
            return_value=httpx.Response(404, json={"detail": "Unknown ticker"})
        )
        with pytest.raises(httpx.HTTPStatusError):
            api_client.download("ZZZZ")


class TestStatements:
    @respx.mock
    def test_get_statement(self, api_client: EdgarAPIClient) -> None:
        respx.get("http://test-api:8000/api/statements/AAPL/income").mock(
            return_value=httpx.Response(200, json={
                "ticker": "AAPL", "statement": "income", "period": "annual",
                "columns": ["fiscal_year", "revenue"], "data": [{"fiscal_year": 2023, "revenue": 383285000000}],
            })
        )
        result = api_client.get_statement("AAPL", "income")
        assert result["ticker"] == "AAPL"
        assert len(result["data"]) == 1


class TestMetrics:
    @respx.mock
    def test_get_available_metrics(self, api_client: EdgarAPIClient) -> None:
        respx.get("http://test-api:8000/api/metrics/available").mock(
            return_value=httpx.Response(200, json={
                "income": ["revenue", "net_income"],
                "balance": ["total_assets"],
                "cashflow": ["operating_cash_flow"],
            })
        )
        result = api_client.get_available_metrics()
        assert "revenue" in result["income"]

    @respx.mock
    def test_get_metric(self, api_client: EdgarAPIClient) -> None:
        respx.get("http://test-api:8000/api/metrics/AAPL/revenue").mock(
            return_value=httpx.Response(200, json={
                "ticker": "AAPL", "metric": "revenue", "period": "annual",
                "data": [
                    {"fiscal_year": 2023, "period_end": "2023-09-30", "value": 383285000000},
                    {"fiscal_year": 2022, "period_end": "2022-09-24", "value": 394328000000},
                ],
            })
        )
        result = api_client.get_metric("AAPL", "revenue")
        assert len(result["data"]) == 2

    @respx.mock
    def test_compare_metrics(self, api_client: EdgarAPIClient) -> None:
        respx.get("http://test-api:8000/api/metrics/AAPL/compare").mock(
            return_value=httpx.Response(200, json={
                "ticker": "AAPL", "metrics": ["revenue", "net_income"], "period": "annual",
                "data": [{"period_end": "2023-09-30", "revenue": 383285000000, "net_income": 96995000000}],
            })
        )
        result = api_client.compare_metrics("AAPL", ["revenue", "net_income"])
        assert result["ticker"] == "AAPL"
        assert len(result["data"]) == 1
