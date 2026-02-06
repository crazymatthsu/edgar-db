"""HTTP client for SEC EDGAR APIs with rate limiting and retries."""

from __future__ import annotations

import time
from typing import Any

import httpx

from .config import Config

BASE_URL = "https://data.sec.gov"
COMPANY_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
COMPANY_FACTS_URL = f"{BASE_URL}/api/xbrl/companyfacts/CIK{{cik}}.json"


class EdgarClient:
    def __init__(self, config: Config) -> None:
        self._config = config
        self._min_interval = 1.0 / config.rate_limit
        self._last_request_time = 0.0
        self._client = httpx.Client(
            headers={
                "User-Agent": config.user_agent,
                "Accept": "application/json",
            },
            timeout=config.timeout,
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> EdgarClient:
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    def _throttle(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last_request_time
        if elapsed < self._min_interval:
            time.sleep(self._min_interval - elapsed)
        self._last_request_time = time.monotonic()

    def _get(self, url: str) -> httpx.Response:
        last_exc: Exception | None = None
        for attempt in range(self._config.max_retries):
            self._throttle()
            try:
                resp = self._client.get(url)
                if resp.status_code == 429:
                    wait = 2 ** attempt
                    time.sleep(wait)
                    continue
                resp.raise_for_status()
                return resp
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code >= 500:
                    last_exc = exc
                    time.sleep(2 ** attempt)
                    continue
                raise
            except httpx.TransportError as exc:
                last_exc = exc
                time.sleep(2 ** attempt)
                continue
        raise last_exc or RuntimeError("Request failed after retries")

    def get_company_tickers(self) -> dict[str, Any]:
        resp = self._get(COMPANY_TICKERS_URL)
        return resp.json()

    def get_company_facts(self, cik: int) -> dict[str, Any]:
        padded = str(cik).zfill(10)
        url = COMPANY_FACTS_URL.format(cik=padded)
        resp = self._get(url)
        return resp.json()

    @staticmethod
    def pad_cik(cik: int) -> str:
        return str(cik).zfill(10)
