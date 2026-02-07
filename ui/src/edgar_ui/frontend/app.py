"""Streamlit frontend for EDGAR Financial Database."""

from __future__ import annotations

import streamlit as st

from edgar_ui.frontend.api_client import EdgarAPIClient
from edgar_ui.frontend.charts import build_chart
from edgar_ui.frontend.formatters import format_number, humanize_metric

st.set_page_config(page_title="EDGAR Financial Database", layout="wide")


@st.cache_resource
def get_client() -> EdgarAPIClient:
    return EdgarAPIClient()


def main() -> None:
    client = get_client()

    # Sidebar
    st.sidebar.title("EDGAR Financial DB")
    ticker = st.sidebar.text_input("Ticker Symbol", value="", placeholder="e.g. AAPL").strip().upper()
    period = st.sidebar.radio("Period", ["Annual", "Quarterly"], index=0)
    period_value = "annual" if period == "Annual" else "quarterly"
    load_btn = st.sidebar.button("Load Data", type="primary", disabled=not ticker)

    # Persist loaded ticker in session state so it survives reruns
    if load_btn and ticker:
        st.session_state["loaded_ticker"] = ticker
    loaded_ticker = st.session_state.get("loaded_ticker")

    # Show DB stats in sidebar
    try:
        stats = client.stats()
        st.sidebar.markdown("---")
        st.sidebar.markdown("**Database Stats**")
        st.sidebar.markdown(f"Companies: {stats['companies']:,}")
        st.sidebar.markdown(f"Facts: {stats['facts']:,}")
        st.sidebar.markdown(f"Tickers: {stats['tickers']:,}")
    except Exception:
        st.sidebar.warning("Could not connect to API backend.")

    # Main area
    st.title("EDGAR Financial Database")

    if not loaded_ticker:
        st.info("Enter a ticker symbol in the sidebar and click 'Load Data' to begin.")
        return

    # Auto-download if needed (only on fresh load)
    if load_btn:
        with st.spinner(f"Loading data for {loaded_ticker}..."):
            try:
                dl_result = client.download(loaded_ticker)
                if dl_result["status"] == "downloaded":
                    st.success(f"Downloaded {dl_result['facts_count']:,} facts for {loaded_ticker}")
            except Exception as e:
                st.error(f"Error loading {loaded_ticker}: {e}")
                return

    # Get available metrics
    try:
        available = client.get_available_metrics()
    except Exception as e:
        st.error(f"Error fetching metrics: {e}")
        return

    # Tabs for each statement type
    tab_income, tab_balance, tab_cashflow = st.tabs(["Income Statement", "Balance Sheet", "Cash Flow"])

    _render_statement_tab(client, tab_income, loaded_ticker, "income", available["income"], period_value)
    _render_statement_tab(client, tab_balance, loaded_ticker, "balance", available["balance"], period_value)
    _render_statement_tab(client, tab_cashflow, loaded_ticker, "cashflow", available["cashflow"], period_value)


def _render_statement_tab(
    client: EdgarAPIClient,
    tab,
    ticker: str,
    statement: str,
    metrics: list[str],
    period: str,
) -> None:
    with tab:
        selected = []
        cols = st.columns(3)
        for i, metric in enumerate(metrics):
            col = cols[i % 3]
            if col.checkbox(humanize_metric(metric), key=f"{statement}_{metric}"):
                selected.append(metric)

        if not selected:
            st.info("Select metrics above to display charts.")
            return

        for metric in selected:
            try:
                result = client.get_metric(ticker, metric, period=period)
                fig = build_chart(metric, result["data"])
                st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.error(f"Error loading {humanize_metric(metric)}: {e}")


if __name__ == "__main__":
    main()
