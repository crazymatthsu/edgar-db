"""Click CLI for edgar-db."""

from __future__ import annotations

import sys

import click
from rich.console import Console
from rich.table import Table

from .config import Config
from .db import connect_db, get_db_stats
from .query import EdgarQuery


console = Console()


def _get_config(**overrides: object) -> Config:
    try:
        return Config(**{k: v for k, v in overrides.items() if v is not None})
    except ValueError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        sys.exit(1)


@click.group()
@click.version_option(version="0.1.0")
def cli() -> None:
    """EDGAR Financial Database — download SEC data into SQLite."""


@cli.command()
@click.option("--ticker", "-t", multiple=True, help="Ticker(s) to download")
@click.option("--sp500", is_flag=True, help="Download all S&P 500 companies")
@click.option("--force", is_flag=True, help="Re-download even if recent")
def download(ticker: tuple[str, ...], sp500: bool, force: bool) -> None:
    """Download company financial data from SEC EDGAR."""
    from .client import EdgarClient
    from .downloader import download_batch, download_company
    from .sp500 import get_sp500_tickers

    if not ticker and not sp500:
        console.print("[red]Error:[/red] Provide --ticker or --sp500")
        sys.exit(1)

    config = _get_config()
    config.ensure_db_dir()
    conn = connect_db(config.db_path)

    tickers: list[str] = list(ticker)
    if sp500:
        console.print("Fetching S&P 500 ticker list...")
        tickers = get_sp500_tickers()
        console.print(f"Found {len(tickers)} tickers")

    def progress(msg: str, current: int, total: int) -> None:
        if msg.startswith("ERROR"):
            console.print(f"  [red]{msg}[/red]")
        else:
            console.print(f"  [{current}/{total}] {msg}")

    with EdgarClient(config) as client:
        if len(tickers) == 1 and not sp500:
            t = tickers[0]
            console.print(f"Downloading {t}...")
            try:
                count = download_company(conn, client, t, force=force)
                if count == 0:
                    console.print(f"  {t}: already up to date (use --force to re-download)")
                else:
                    console.print(f"  {t}: stored {count} facts")
            except Exception as exc:
                console.print(f"  [red]Error: {exc}[/red]")
                sys.exit(1)
        else:
            results = download_batch(
                conn, client, tickers, force=force, progress_callback=progress
            )
            success = sum(1 for v in results.values() if v >= 0)
            errors = sum(1 for v in results.values() if v < 0)
            console.print(f"\nDone: {success} succeeded, {errors} failed")

    conn.close()


@cli.command()
@click.argument("ticker")
@click.option(
    "--statement", "-s",
    type=click.Choice(["income", "balance", "cashflow", "all"]),
    default="all",
    help="Which statement to show",
)
@click.option(
    "--period", "-p",
    type=click.Choice(["annual", "quarterly"]),
    default="annual",
    help="Annual (10-K) or quarterly (10-Q)",
)
@click.option(
    "--format", "fmt",
    type=click.Choice(["table", "csv"]),
    default="table",
    help="Output format",
)
def show(ticker: str, statement: str, period: str, fmt: str) -> None:
    """Show financial statements for a ticker."""
    config = _get_config()
    conn = connect_db(config.db_path)
    q = EdgarQuery(conn)

    statements = (
        ["income", "balance", "cashflow"] if statement == "all" else [statement]
    )

    for stmt in statements:
        if stmt == "income":
            df = q.get_income_statement(ticker, period)
            title = "Income Statement"
        elif stmt == "balance":
            df = q.get_balance_sheet(ticker, period)
            title = "Balance Sheet"
        else:
            df = q.get_cash_flow(ticker, period)
            title = "Cash Flow Statement"

        if df.empty:
            console.print(f"[yellow]No {title.lower()} data for {ticker.upper()}[/yellow]")
            continue

        if fmt == "csv":
            click.echo(df.to_csv(index=False))
        else:
            _print_rich_table(df, f"{ticker.upper()} — {title} ({period})")

    conn.close()


def _print_rich_table(df: "import('pandas').DataFrame", title: str) -> None:
    table = Table(title=title, show_lines=True)

    for col in df.columns:
        table.add_column(str(col), justify="right" if col not in ("fiscal_year", "fiscal_period", "period_end") else "left")

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

    table = Table(title="EDGAR Database Info")
    table.add_column("Metric", style="bold")
    table.add_column("Value", justify="right")
    table.add_row("Companies", str(stats["companies"]))
    table.add_row("Total Facts", str(stats["facts"]))
    table.add_row("Tickers Mapped", str(stats["tickers"]))
    table.add_row("Statement Types", str(stats["statements"]))
    table.add_row("Database Path", str(config.db_path))

    console.print(table)
    conn.close()
