"""Plotly chart builders for financial metrics."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from .formatters import format_number, humanize_metric

# Metric categories for chart type selection
_LINE_METRICS = {
    "eps_basic", "eps_diluted", "dividends_per_share",
}

_AREA_METRICS = {
    "shares_basic", "shares_diluted", "common_stock_shares",
}

_CASHFLOW_BAR_METRICS = {
    "operating_cash_flow", "free_cash_flow", "investing_cash_flow",
    "financing_cash_flow", "capital_expenditure", "dividends_paid",
    "share_repurchase",
}


def build_chart(metric: str, data: list[dict]) -> go.Figure:
    """Build the appropriate Plotly chart for a given metric and data.

    Args:
        metric: Canonical metric name (e.g., "revenue", "eps_basic")
        data: List of dicts with fiscal_year, period_end, value keys

    Returns:
        Plotly Figure object
    """
    if not data:
        fig = go.Figure()
        fig.update_layout(title=humanize_metric(metric), annotations=[
            dict(text="No data available", xref="paper", yref="paper",
                 x=0.5, y=0.5, showarrow=False, font=dict(size=16))
        ])
        return fig

    df = pd.DataFrame(data)
    df = df.sort_values("period_end", ascending=True)
    df["label"] = df["fiscal_year"].astype(str)

    title = humanize_metric(metric)

    if metric in _LINE_METRICS:
        return _build_line_chart(df, title)
    elif metric in _AREA_METRICS:
        return _build_area_chart(df, title)
    elif metric in _CASHFLOW_BAR_METRICS:
        return _build_cashflow_bar(df, title)
    else:
        return _build_bar_chart(df, title)


def _build_bar_chart(df: pd.DataFrame, title: str) -> go.Figure:
    fig = px.bar(df, x="label", y="value", title=title)
    fig.update_layout(
        xaxis_title="Fiscal Year",
        yaxis_title="USD",
        hovermode="x unified",
    )
    fig.update_traces(
        hovertemplate="%{y:,.0f}<extra></extra>",
    )
    return fig


def _build_line_chart(df: pd.DataFrame, title: str) -> go.Figure:
    fig = px.line(df, x="label", y="value", title=title, markers=True)
    fig.update_layout(
        xaxis_title="Fiscal Year",
        yaxis_title="Value",
        hovermode="x unified",
    )
    fig.update_traces(
        hovertemplate="%{y:,.2f}<extra></extra>",
    )
    return fig


def _build_area_chart(df: pd.DataFrame, title: str) -> go.Figure:
    fig = px.area(df, x="label", y="value", title=title)
    fig.update_layout(
        xaxis_title="Fiscal Year",
        yaxis_title="Shares",
        hovermode="x unified",
    )
    fig.update_traces(
        hovertemplate="%{y:,.0f}<extra></extra>",
    )
    return fig


def _build_cashflow_bar(df: pd.DataFrame, title: str) -> go.Figure:
    colors = ["#2ca02c" if v >= 0 else "#d62728" for v in df["value"]]
    fig = go.Figure(
        data=[go.Bar(
            x=df["label"],
            y=df["value"],
            marker_color=colors,
            hovertemplate="%{y:,.0f}<extra></extra>",
        )]
    )
    fig.update_layout(
        title=title,
        xaxis_title="Fiscal Year",
        yaxis_title="USD",
        hovermode="x unified",
    )
    return fig
