"""Tests for statement endpoints."""

from __future__ import annotations

from fastapi.testclient import TestClient


class TestStatements:
    def test_income_statement(self, client: TestClient) -> None:
        resp = client.get("/api/statements/AAPL/income")
        assert resp.status_code == 200
        data = resp.json()
        assert data["ticker"] == "AAPL"
        assert data["statement"] == "income"
        assert data["period"] == "annual"
        assert "revenue" in data["columns"]
        assert len(data["data"]) > 0

    def test_balance_sheet(self, client: TestClient) -> None:
        resp = client.get("/api/statements/AAPL/balance")
        assert resp.status_code == 200
        data = resp.json()
        assert data["statement"] == "balance"
        assert "total_assets" in data["columns"]

    def test_cashflow(self, client: TestClient) -> None:
        resp = client.get("/api/statements/AAPL/cashflow")
        assert resp.status_code == 200
        data = resp.json()
        assert data["statement"] == "cashflow"
        assert "operating_cash_flow" in data["columns"]

    def test_quarterly_period(self, client: TestClient) -> None:
        resp = client.get("/api/statements/AAPL/income?period=quarterly")
        assert resp.status_code == 200
        data = resp.json()
        assert data["period"] == "quarterly"

    def test_unknown_ticker_404(self, client: TestClient) -> None:
        resp = client.get("/api/statements/ZZZZ/income")
        assert resp.status_code == 404

    def test_invalid_statement_type(self, client: TestClient) -> None:
        resp = client.get("/api/statements/AAPL/invalid")
        assert resp.status_code == 400

    def test_nan_becomes_null(self, client: TestClient) -> None:
        resp = client.get("/api/statements/AAPL/income")
        data = resp.json()
        # Check that no NaN strings appear in the JSON
        for row in data["data"]:
            for val in row.values():
                assert val != "NaN"

    def test_case_insensitive_ticker(self, client: TestClient) -> None:
        resp = client.get("/api/statements/aapl/income")
        assert resp.status_code == 200
        assert resp.json()["ticker"] == "AAPL"

    def test_empty_data(self, client: TestClient) -> None:
        # MSFT has no balance sheet data in our test fixture
        resp = client.get("/api/statements/MSFT/balance")
        assert resp.status_code == 200
        data = resp.json()
        assert data["data"] == []
        assert data["columns"] == []
