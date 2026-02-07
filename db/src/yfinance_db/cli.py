"""Click CLI for yfinance-db."""

from __future__ import annotations

import sys

import click
from rich.console import Console
from rich.table import Table

from .config import Config
from .db import connect_db, get_db_stats
from .query import YFinanceQuery

console = Console()


def _get_config(**overrides: object) -> Config:
    return Config(**{k: v for k, v in overrides.items() if v is not None})


@click.group()
@click.version_option(version="0.1.0")
def cli() -> None:
    """Yahoo Finance Database — download market data into SQLite."""


@cli.command()
@click.option("--ticker", "-t", multiple=True, help="Ticker(s) to download")
@click.option("--force", is_flag=True, help="Re-download even if recent")
@click.option("--period", "-p", default="5y", help="Price history period (1y, 2y, 5y, 10y, max)")
def download(ticker: tuple[str, ...], force: bool, period: str) -> None:
    """Download company data from Yahoo Finance."""
    if not ticker:
        console.print("[red]Error:[/red] Provide at least one --ticker")
        sys.exit(1)

    config = _get_config()
    config.ensure_db_dir()
    conn = connect_db(config.db_path)

    from .client import YFinanceClient
    from .downloader import download_batch, download_company

    client = YFinanceClient(config)
    tickers = list(ticker)

    if len(tickers) == 1:
        t = tickers[0]
        console.print(f"Downloading {t}...")
        try:
            counts = download_company(conn, client, t, force=force, period=period)
            if not counts:
                console.print(f"  {t}: already up to date (use --force to re-download)")
            else:
                total = sum(v for v in counts.values() if v > 0)
                console.print(f"  {t}: stored {total} records")
        except Exception as exc:
            console.print(f"  [red]Error: {exc}[/red]")
            sys.exit(1)
    else:
        def progress(msg: str, current: int, total: int) -> None:
            if msg.startswith("ERROR"):
                console.print(f"  [red]{msg}[/red]")
            else:
                console.print(f"  [{current}/{total}] {msg}")

        results = download_batch(
            conn, client, tickers, force=force, period=period,
            progress_callback=progress,
        )
        success = sum(1 for v in results.values() if "error" not in v)
        errors = sum(1 for v in results.values() if "error" in v)
        console.print(f"\nDone: {success} succeeded, {errors} failed")

    conn.close()


@cli.command()
@click.argument("ticker")
@click.option(
    "--data", "-d",
    type=click.Choice(["prices", "income", "balance", "cashflow", "dividends", "splits", "stats", "all"]),
    default="all",
    help="Which data to show",
)
@click.option(
    "--period", "-p",
    type=click.Choice(["annual", "quarterly"]),
    default="annual",
    help="Annual or quarterly (for financials)",
)
@click.option(
    "--format", "fmt",
    type=click.Choice(["table", "csv"]),
    default="table",
    help="Output format",
)
def show(ticker: str, data: str, period: str, fmt: str) -> None:
    """Show data for a ticker."""
    config = _get_config()
    conn = connect_db(config.db_path)
    q = YFinanceQuery(conn)

    sections = {
        "prices": ("Prices", lambda: q.get_prices(ticker)),
        "income": ("Income Statement", lambda: q.get_income_statement(ticker, period)),
        "balance": ("Balance Sheet", lambda: q.get_balance_sheet(ticker, period)),
        "cashflow": ("Cash Flow", lambda: q.get_cash_flow(ticker, period)),
        "dividends": ("Dividends", lambda: q.get_dividends(ticker)),
        "splits": ("Splits", lambda: q.get_splits(ticker)),
        "stats": ("Company Stats", lambda: q.get_stats(ticker)),
    }

    show_sections = list(sections.keys()) if data == "all" else [data]

    for key in show_sections:
        title, fetcher = sections[key]
        try:
            df = fetcher()
        except ValueError as exc:
            console.print(f"[red]Error:[/red] {exc}")
            continue

        if df.empty:
            console.print(f"[yellow]No {title.lower()} data for {ticker.upper()}[/yellow]")
            continue

        if fmt == "csv":
            click.echo(df.to_csv(index=False))
        else:
            _print_rich_table(df, f"{ticker.upper()} — {title} ({period})")

    conn.close()


def _print_rich_table(df: "pd.DataFrame", title: str) -> None:
    table = Table(title=title, show_lines=True)

    non_numeric = {"date", "period_end", "ticker", "fetched_date", "id"}
    for col in df.columns:
        justify = "left" if col in non_numeric else "right"
        table.add_column(str(col), justify=justify)

    for _, row in df.head(20).iterrows():
        cells = []
        for col in df.columns:
            val = row[col]
            if isinstance(val, float):
                if abs(val) >= 1e9:
                    cells.append(f"{val/1e9:,.2f}B")
                elif abs(val) >= 1e6:
                    cells.append(f"{val/1e6:,.2f}M")
                elif abs(val) >= 1e3:
                    cells.append(f"{val/1e3:,.2f}K")
                else:
                    cells.append(f"{val:,.2f}")
            else:
                cells.append(str(val) if val is not None else "")
        table.add_row(*cells)

    console.print(table)
    console.print()


@cli.command()
def info() -> None:
    """Show database statistics."""
    config = _get_config()
    conn = connect_db(config.db_path)
    stats = get_db_stats(conn)

    table = Table(title="Yahoo Finance Database Info")
    table.add_column("Metric", style="bold")
    table.add_column("Value", justify="right")
    table.add_row("Companies", str(stats["companies"]))
    table.add_row("Price Records", str(stats["prices"]))
    table.add_row("Financial Records", str(stats["financials"]))
    table.add_row("Stat Snapshots", str(stats["stat_snapshots"]))
    table.add_row("Dividends", str(stats["dividends"]))
    table.add_row("Splits", str(stats["splits"]))
    table.add_row("Database Path", str(config.db_path))

    console.print(table)
    conn.close()
