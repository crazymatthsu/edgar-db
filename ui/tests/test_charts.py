"""Tests for Plotly chart builders."""

from __future__ import annotations

import plotly.graph_objects as go

from ui.frontend.charts import build_chart


class TestBuildChart:
    def _sample_data(self) -> list[dict]:
        return [
            {"fiscal_year": 2021, "period_end": "2021-09-25", "value": 365817000000},
            {"fiscal_year": 2022, "period_end": "2022-09-24", "value": 394328000000},
            {"fiscal_year": 2023, "period_end": "2023-09-30", "value": 383285000000},
        ]

    def test_revenue_returns_bar(self) -> None:
        fig = build_chart("revenue", self._sample_data())
        assert isinstance(fig, go.Figure)
        assert len(fig.data) > 0
        assert isinstance(fig.data[0], go.Bar)

    def test_eps_returns_line(self) -> None:
        data = [
            {"fiscal_year": 2022, "period_end": "2022-09-24", "value": 6.15},
            {"fiscal_year": 2023, "period_end": "2023-09-30", "value": 6.13},
        ]
        fig = build_chart("eps_basic", data)
        assert isinstance(fig, go.Figure)
        assert isinstance(fig.data[0], go.Scatter)

    def test_shares_returns_area(self) -> None:
        data = [
            {"fiscal_year": 2022, "period_end": "2022-09-24", "value": 16000000000},
            {"fiscal_year": 2023, "period_end": "2023-09-30", "value": 15500000000},
        ]
        fig = build_chart("shares_basic", data)
        assert isinstance(fig, go.Figure)
        assert isinstance(fig.data[0], go.Scatter)
        assert fig.data[0].stackgroup is not None  # area chart uses stackgroup

    def test_cashflow_bar_has_colors(self) -> None:
        data = [
            {"fiscal_year": 2022, "period_end": "2022-09-24", "value": 110000000000},
            {"fiscal_year": 2023, "period_end": "2023-09-30", "value": -5000000000},
        ]
        fig = build_chart("operating_cash_flow", data)
        assert isinstance(fig, go.Figure)
        assert isinstance(fig.data[0], go.Bar)
        colors = fig.data[0].marker.color
        assert "#2ca02c" in colors  # green for positive
        assert "#d62728" in colors  # red for negative

    def test_empty_data(self) -> None:
        fig = build_chart("revenue", [])
        assert isinstance(fig, go.Figure)
        assert len(fig.data) == 0  # no data traces

    def test_total_assets_returns_bar(self) -> None:
        data = [
            {"fiscal_year": 2023, "period_end": "2023-09-30", "value": 352583000000},
        ]
        fig = build_chart("total_assets", data)
        assert isinstance(fig, go.Figure)
        assert isinstance(fig.data[0], go.Bar)

    def test_chart_has_title(self) -> None:
        fig = build_chart("net_income", self._sample_data())
        assert "Net Income" in fig.layout.title.text
