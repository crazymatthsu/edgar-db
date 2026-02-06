"""Tests for health and stats endpoints."""

from __future__ import annotations

from fastapi.testclient import TestClient


class TestHealth:
    def test_health_ok(self, client: TestClient) -> None:
        resp = client.get("/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert "db_path" in data

    def test_stats(self, client: TestClient) -> None:
        resp = client.get("/api/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert data["companies"] == 2
        assert data["facts"] > 0
        assert data["tickers"] == 2
        assert data["statements"] > 0
