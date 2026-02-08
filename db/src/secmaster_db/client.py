"""Security master clients: yfinance for company info, OpenFIGI for identifiers."""

from __future__ import annotations

import time
from typing import Any

import httpx

from .config import Config


def _import_yf():
    import yfinance as yf
    return yf


_OPENFIGI_URL = "https://api.openfigi.com/v3/mapping"


class YFinanceClient:
    def __init__(self, config: Config) -> None:
        self._config = config
        self._min_interval = 1.0 / config.rate_limit
        self._last_request_time = 0.0
        self._yf = _import_yf()

    def _throttle(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last_request_time
        if elapsed < self._min_interval:
            time.sleep(self._min_interval - elapsed)
        self._last_request_time = time.monotonic()

    def _retry(self, func: Any, *args: Any, **kwargs: Any) -> Any:
        last_exc: Exception | None = None
        for attempt in range(self._config.max_retries):
            self._throttle()
            try:
                return func(*args, **kwargs)
            except Exception as exc:
                last_exc = exc
                time.sleep(2 ** attempt)
                continue
        raise last_exc or RuntimeError("Request failed after retries")

    def get_info(self, ticker: str) -> dict[str, Any]:
        def _fetch() -> dict[str, Any]:
            t = self._yf.Ticker(ticker)
            info = t.info
            if not info or info.get("regularMarketPrice") is None:
                raise ValueError(f"No data returned for {ticker}")
            return info
        return self._retry(_fetch)


class OpenFIGIClient:
    def __init__(self, config: Config) -> None:
        self._config = config
        self._min_interval = 60.0 / (250.0 if config.openfigi_api_key else 25.0)
        self._last_request_time = 0.0

    def _throttle(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last_request_time
        if elapsed < self._min_interval:
            time.sleep(self._min_interval - elapsed)
        self._last_request_time = time.monotonic()

    def fetch_figi(self, ticker: str) -> dict[str, Any] | None:
        self._throttle()
        headers: dict[str, str] = {"Content-Type": "application/json"}
        if self._config.openfigi_api_key:
            headers["X-OPENFIGI-APIKEY"] = self._config.openfigi_api_key

        payload = [{"idType": "TICKER", "idValue": ticker, "exchCode": "US"}]

        try:
            resp = httpx.post(
                _OPENFIGI_URL,
                json=payload,
                headers=headers,
                timeout=self._config.timeout,
            )
            resp.raise_for_status()
            data = resp.json()
            if data and isinstance(data, list) and "data" in data[0]:
                return data[0]["data"][0]
        except Exception:
            pass
        return None
