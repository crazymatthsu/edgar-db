from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass
class FactRow:
    cik: int
    tag: str
    canonical_name: str
    statement: str
    value: float
    unit: str
    period_end: str  # ISO date string YYYY-MM-DD
    fiscal_year: int
    fiscal_period: str  # FY, Q1, Q2, Q3, Q4
    form: str  # 10-K, 10-Q
    filed: str  # ISO date string
    accession: str


@dataclass
class Company:
    cik: int
    name: str
    ticker: str
    sic: str = ""
    exchanges: str = ""
    last_downloaded: str = ""  # ISO datetime
