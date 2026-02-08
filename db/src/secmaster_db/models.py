from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SecurityRow:
    ticker: str
    name: str = ""
    isin: str = ""
    cusip: str = ""
    sedol: str = ""
    primary_ric: str = ""
    bloomberg_code: str = ""
    figi: str = ""
    share_class_figi: str = ""
    shares_outstanding: int = 0
    country: str = ""
    exchange_mic: str = ""
    exchange_currency: str = ""
    sector: str = ""
    industry: str = ""
    market_cap: float = 0.0
    style_box: str = ""
    last_updated: str = ""
