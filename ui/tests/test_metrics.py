"""Tests for metric endpoints."""

from __future__ import annotations

from fastapi.testclient import TestClient


class TestAvailableMetrics:
    def test_returns_all_statements(self, client: TestClient) -> None:
        resp = client.get("/api/metrics/available")
        assert resp.status_code == 200
        data = resp.json()
        assert "income" in data
        assert "balance" in data
        assert "cashflow" in data
        assert "revenue" in data["income"]
        assert "total_assets" in data["balance"]
        assert "operating_cash_flow" in data["cashflow"]


class TestGetMetric:
    def test_single_metric(self, client: TestClient) -> None:
        resp = client.get("/api/metrics/AAPL/revenue")
        assert resp.status_code == 200
        data = resp.json()
        assert data["ticker"] == "AAPL"
        assert data["metric"] == "revenue"
        assert len(data["data"]) == 2  # 2 annual years

    def test_metric_data_has_value(self, client: TestClient) -> None:
        resp = client.get("/api/metrics/AAPL/revenue")
        data = resp.json()
        for row in data["data"]:
            assert "value" in row
            assert "fiscal_year" in row
            assert "period_end" in row

    def test_unknown_ticker_404(self, client: TestClient) -> None:
        resp = client.get("/api/metrics/ZZZZ/revenue")
        assert resp.status_code == 404

    def test_quarterly_period(self, client: TestClient) -> None:
        resp = client.get("/api/metrics/AAPL/revenue?period=quarterly")
        assert resp.status_code == 200
        data = resp.json()
        assert data["period"] == "quarterly"


class TestCompareMetrics:
    def test_compare_two_metrics(self, client: TestClient) -> None:
        resp = client.get("/api/metrics/AAPL/compare?metrics=revenue,net_income")
        assert resp.status_code == 200
        data = resp.json()
        assert data["ticker"] == "AAPL"
        assert data["metrics"] == ["revenue", "net_income"]
        assert len(data["data"]) > 0
        # Each row should have period_end and metric values
        row = data["data"][0]
        assert "period_end" in row
        assert "revenue" in row
        assert "net_income" in row

    def test_compare_unknown_ticker_404(self, client: TestClient) -> None:
        resp = client.get("/api/metrics/ZZZZ/compare?metrics=revenue")
        assert resp.status_code == 404

    def test_compare_no_metrics_400(self, client: TestClient) -> None:
        resp = client.get("/api/metrics/AAPL/compare?metrics=")
        assert resp.status_code == 400
