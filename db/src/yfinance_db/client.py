"""Yahoo Finance client wrapping yfinance with rate limiting and retries."""

from __future__ import annotations

import time
from typing import Any

import pandas as pd

from .config import Config


def _import_yf():
    import yfinance as yf
    return yf


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
                result = func(*args, **kwargs)
                return result
            except Exception as exc:
                last_exc = exc
                time.sleep(2 ** attempt)
                continue
        raise last_exc or RuntimeError("Request failed after retries")

    def _ticker(self, symbol: str) -> Any:
        return self._yf.Ticker(symbol)

    def get_info(self, ticker: str) -> dict[str, Any]:
        def _fetch() -> dict[str, Any]:
            t = self._ticker(ticker)
            info = t.info
            if not info or info.get("regularMarketPrice") is None:
                raise ValueError(f"No data returned for {ticker}")
            return info
        return self._retry(_fetch)

    def get_history(
        self, ticker: str, period: str = "5y", interval: str = "1d"
    ) -> pd.DataFrame:
        def _fetch() -> pd.DataFrame:
            t = self._ticker(ticker)
            df = t.history(period=period, interval=interval)
            if df.empty:
                raise ValueError(f"No price history for {ticker}")
            return df
        return self._retry(_fetch)

    def get_income_statement(
        self, ticker: str, quarterly: bool = False
    ) -> pd.DataFrame:
        def _fetch() -> pd.DataFrame:
            t = self._ticker(ticker)
            return t.quarterly_income_stmt if quarterly else t.income_stmt
        return self._retry(_fetch)

    def get_balance_sheet(
        self, ticker: str, quarterly: bool = False
    ) -> pd.DataFrame:
        def _fetch() -> pd.DataFrame:
            t = self._ticker(ticker)
            return t.quarterly_balance_sheet if quarterly else t.balance_sheet
        return self._retry(_fetch)

    def get_cashflow(
        self, ticker: str, quarterly: bool = False
    ) -> pd.DataFrame:
        def _fetch() -> pd.DataFrame:
            t = self._ticker(ticker)
            return t.quarterly_cashflow if quarterly else t.cashflow
        return self._retry(_fetch)

    def get_dividends(self, ticker: str) -> pd.Series:
        def _fetch() -> pd.Series:
            t = self._ticker(ticker)
            return t.dividends
        return self._retry(_fetch)

    def get_splits(self, ticker: str) -> pd.Series:
        def _fetch() -> pd.Series:
            t = self._ticker(ticker)
            return t.splits
        return self._retry(_fetch)
