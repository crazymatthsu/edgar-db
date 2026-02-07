"""Metric endpoints — optimized for charting."""

from __future__ import annotations

import pandas as pd
from fastapi import APIRouter, HTTPException, Query

from edgar_db.xbrl_tags import STATEMENT_COLUMNS

from ..dependencies import get_query
from ..schemas import AvailableMetricsResponse, CompareResponse, MetricSeriesResponse

router = APIRouter(prefix="/api/metrics", tags=["metrics"])


@router.get("/available", response_model=AvailableMetricsResponse)
def available_metrics():
    return AvailableMetricsResponse(
        income=STATEMENT_COLUMNS["income"],
        balance=STATEMENT_COLUMNS["balance"],
        cashflow=STATEMENT_COLUMNS["cashflow"],
    )


@router.get("/{ticker}/compare", response_model=CompareResponse)
def compare_metrics(
    ticker: str,
    metrics: str = Query(..., description="Comma-separated metric names"),
    period: str = Query("annual", pattern="^(annual|quarterly)$"),
):
    metric_list = [m.strip() for m in metrics.split(",") if m.strip()]
    if not metric_list:
        raise HTTPException(status_code=400, detail="No metrics specified")

    query = get_query()

    frames = {}
    for metric in metric_list:
        try:
            df = query.get_metric(ticker, metric, period=period)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
        if not df.empty:
            series = df.set_index("period_end")["value"]
            series.name = metric
            frames[metric] = series

    if not frames:
        return CompareResponse(
            ticker=ticker.upper(),
            metrics=metric_list,
            period=period,
            data=[],
        )

    merged = pd.DataFrame(frames)
    merged.index.name = "period_end"
    merged = merged.sort_index(ascending=False).reset_index()
    data = merged.where(merged.notna(), None).to_dict(orient="records")

    return CompareResponse(
        ticker=ticker.upper(),
        metrics=metric_list,
        period=period,
        data=data,
    )


@router.get("/{ticker}/{metric}", response_model=MetricSeriesResponse)
def get_metric(
    ticker: str,
    metric: str,
    period: str = Query("annual", pattern="^(annual|quarterly)$"),
):
    query = get_query()
    try:
        df = query.get_metric(ticker, metric, period=period)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    data = df.where(df.notna(), None).to_dict(orient="records")

    return MetricSeriesResponse(
        ticker=ticker.upper(),
        metric=metric,
        period=period,
        data=data,
    )
