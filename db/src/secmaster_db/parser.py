"""Parse yfinance and OpenFIGI responses into SecurityRow."""

from __future__ import annotations

from typing import Any

from .models import SecurityRow


def classify_style_box(market_cap: float) -> str:
    if market_cap >= 10_000_000_000:
        return "large_cap"
    elif market_cap >= 2_000_000_000:
        return "mid_cap"
    else:
        return "small_cap"


def parse_yfinance_info(ticker: str, info: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": info.get("longName") or info.get("shortName", ticker),
        "isin": info.get("isin", ""),
        "shares_outstanding": int(info.get("sharesOutstanding", 0) or 0),
        "country": info.get("country", ""),
        "exchange_currency": info.get("currency", ""),
        "sector": info.get("sector", ""),
        "industry": info.get("industry", ""),
        "market_cap": float(info.get("marketCap", 0) or 0),
    }


def parse_openfigi_response(data: dict[str, Any]) -> dict[str, Any]:
    return {
        "figi": data.get("figi", ""),
        "share_class_figi": data.get("shareClassFIGI", ""),
        "exchange_mic": data.get("micCode", ""),
    }


def build_security_row(
    ticker: str,
    yf_data: dict[str, Any],
    figi_data: dict[str, Any] | None,
    last_updated: str,
) -> SecurityRow:
    fields: dict[str, Any] = {"ticker": ticker.upper(), "last_updated": last_updated}
    fields.update(yf_data)

    if figi_data:
        parsed_figi = parse_openfigi_response(figi_data)
        fields.update(parsed_figi)

    market_cap = fields.get("market_cap", 0.0)
    fields["style_box"] = classify_style_box(market_cap)

    return SecurityRow(**fields)
