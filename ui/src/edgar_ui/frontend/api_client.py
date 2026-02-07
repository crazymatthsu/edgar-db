"""HTTP client for the EDGAR FastAPI backend."""

from __future__ import annotations

import os

import httpx


def _base_url() -> str:
    return os.environ.get("EDGAR_API_URL", "http://localhost:8000")


class EdgarAPIClient:
    """Client to interact with the EDGAR REST API backend."""

    def __init__(self, base_url: str | None = None) -> None:
        self.base_url = base_url or _base_url()
        self._client = httpx.Client(base_url=self.base_url, timeout=60.0)

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> EdgarAPIClient:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def health(self) -> dict:
        resp = self._client.get("/api/health")
        resp.raise_for_status()
        return resp.json()

    def stats(self) -> dict:
        resp = self._client.get("/api/stats")
        resp.raise_for_status()
        return resp.json()

    def download(self, ticker: str, force: bool = False) -> dict:
        resp = self._client.post(f"/api/download/{ticker}", params={"force": force})
        resp.raise_for_status()
        return resp.json()

    def get_statement(self, ticker: str, statement_type: str, period: str = "annual") -> dict:
        resp = self._client.get(
            f"/api/statements/{ticker}/{statement_type}",
            params={"period": period},
        )
        resp.raise_for_status()
        return resp.json()

    def get_available_metrics(self) -> dict:
        resp = self._client.get("/api/metrics/available")
        resp.raise_for_status()
        return resp.json()

    def get_metric(self, ticker: str, metric: str, period: str = "annual") -> dict:
        resp = self._client.get(
            f"/api/metrics/{ticker}/{metric}",
            params={"period": period},
        )
        resp.raise_for_status()
        return resp.json()

    def compare_metrics(self, ticker: str, metrics: list[str], period: str = "annual") -> dict:
        resp = self._client.get(
            f"/api/metrics/{ticker}/compare",
            params={"metrics": ",".join(metrics), "period": period},
        )
        resp.raise_for_status()
        return resp.json()
