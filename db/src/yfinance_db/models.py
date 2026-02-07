from __future__ import annotations

from dataclasses import dataclass


@dataclass
class CompanyRow:
    ticker: str
    name: str
    sector: str = ""
    industry: str = ""
    market_cap: float = 0.0
    last_downloaded: str = ""  # ISO datetime


@dataclass
class PriceRow:
    ticker: str
    date: str  # ISO date YYYY-MM-DD
    interval: str  # 1d, 1wk, 1mo
    open: float
    high: float
    low: float
    close: float
    volume: int


@dataclass
class CompanyStatRow:
    ticker: str
    fetched_date: str  # ISO date YYYY-MM-DD
    market_cap: float = 0.0
    pe_ratio: float = 0.0
    forward_pe: float = 0.0
    peg_ratio: float = 0.0
    price_to_book: float = 0.0
    enterprise_value: float = 0.0
    ev_to_ebitda: float = 0.0
    profit_margin: float = 0.0
    operating_margin: float = 0.0
    roe: float = 0.0
    roa: float = 0.0
    revenue_growth: float = 0.0
    earnings_growth: float = 0.0
    dividend_yield: float = 0.0
    beta: float = 0.0
    fifty_two_week_high: float = 0.0
    fifty_two_week_low: float = 0.0
    avg_volume: int = 0
    shares_outstanding: int = 0
    float_shares: int = 0
    short_ratio: float = 0.0


@dataclass
class FinancialRow:
    ticker: str
    statement: str  # income, balance, cashflow
    period_type: str  # annual, quarterly
    period_end: str  # ISO date YYYY-MM-DD
    metric: str
    value: float


@dataclass
class DividendRow:
    ticker: str
    date: str  # ISO date YYYY-MM-DD
    amount: float


@dataclass
class SplitRow:
    ticker: str
    date: str  # ISO date YYYY-MM-DD
    ratio: float
