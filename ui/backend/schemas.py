"""Pydantic response models for the REST API."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    db_path: str


class StatsResponse(BaseModel):
    companies: int
    facts: int
    tickers: int
    statements: int


class DownloadResponse(BaseModel):
    ticker: str
    status: str
    facts_count: int


class StatementResponse(BaseModel):
    ticker: str
    statement: str
    period: str
    columns: list[str]
    data: list[dict[str, Any]]


class AvailableMetricsResponse(BaseModel):
    income: list[str]
    balance: list[str]
    cashflow: list[str]


class MetricSeriesResponse(BaseModel):
    ticker: str
    metric: str
    period: str
    data: list[dict[str, Any]]


class CompareResponse(BaseModel):
    ticker: str
    metrics: list[str]
    period: str
    data: list[dict[str, Any]]
