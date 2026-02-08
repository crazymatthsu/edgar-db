"""Click CLI for secmaster-db."""

from __future__ import annotations

import sys

import click
from rich.console import Console
from rich.table import Table

from .config import Config
from .db import connect_db, get_db_stats
from .query import SecMasterQuery

console = Console()


def _get_config(**overrides: object) -> Config:
    return Config(**{k: v for k, v in overrides.items() if v is not None})


@click.group()
@click.version_option(version="0.1.0")
def cli() -> None:
    """Security Master Database — download security reference data into SQLite."""


@cli.command()
@click.option("--ticker", "-t", multiple=True, help="Ticker(s) to download")
@click.option("--sp500", is_flag=True, help="Download all S&P 500 companies")
@click.option("--force", is_flag=True, help="Re-download even if recent")
@click.option("--no-figi", is_flag=True, help="Skip OpenFIGI lookup")
def download(ticker: tuple[str, ...], sp500: bool, force: bool, no_figi: bool) -> None:
    """Download security reference data."""
    if not ticker and not sp500:
        console.print("[red]Error:[/red] Provide --ticker or --sp500")
        sys.exit(1)

    config = _get_config()
    config.ensure_db_dir()
    conn = connect_db(config.db_path)

    from .client import OpenFIGIClient, YFinanceClient
    from .downloader import download_batch, download_security

    yf_client = YFinanceClient(config)
    figi_client = None if no_figi else OpenFIGIClient(config)

    tickers: list[str] = list(ticker)
    if sp500:
        from edgar_db.sp500 import get_sp500_tickers

        console.print("Fetching S&P 500 ticker list...")
        tickers = get_sp500_tickers()
        console.print(f"Found {len(tickers)} tickers")

    if len(tickers) == 1:
        t = tickers[0]
        console.print(f"Downloading {t}...")
        try:
            downloaded = download_security(conn, yf_client, figi_client, t, force=force)
            if not downloaded:
                console.print(f"  {t}: already up to date (use --force to re-download)")
            else:
                console.print(f"  {t}: done")
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
            conn, yf_client, figi_client, tickers, force=force,
            progress_callback=progress,
        )
        success = sum(1 for v in results.values() if isinstance(v, bool))
        errors = sum(1 for v in results.values() if isinstance(v, str))
        console.print(f"\nDone: {success} succeeded, {errors} failed")

    conn.close()


@cli.command()
@click.argument("ticker")
def show(ticker: str) -> None:
    """Show security details for a ticker."""
    config = _get_config()
    conn = connect_db(config.db_path)
    q = SecMasterQuery(conn)

    sec = q.get_security(ticker)
    if sec is None:
        console.print(f"[yellow]No data for {ticker.upper()}. Try downloading first.[/yellow]")
        conn.close()
        return

    table = Table(title=f"{sec.ticker} — {sec.name}")
    table.add_column("Field", style="bold")
    table.add_column("Value")

    fields = [
        ("Ticker", sec.ticker),
        ("Name", sec.name),
        ("ISIN", sec.isin),
        ("CUSIP", sec.cusip),
        ("SEDOL", sec.sedol),
        ("Primary RIC", sec.primary_ric),
        ("Bloomberg Code", sec.bloomberg_code),
        ("FIGI", sec.figi),
        ("Share Class FIGI", sec.share_class_figi),
        ("Shares Outstanding", f"{sec.shares_outstanding:,}"),
        ("Country", sec.country),
        ("Exchange MIC", sec.exchange_mic),
        ("Currency", sec.exchange_currency),
        ("Sector", sec.sector),
        ("Industry", sec.industry),
        ("Market Cap", _format_market_cap(sec.market_cap)),
        ("Style Box", sec.style_box),
        ("Last Updated", sec.last_updated),
    ]

    for label, value in fields:
        table.add_row(label, str(value) if value else "")

    console.print(table)
    conn.close()


def _format_market_cap(cap: float) -> str:
    if cap >= 1e12:
        return f"${cap/1e12:,.2f}T"
    elif cap >= 1e9:
        return f"${cap/1e9:,.2f}B"
    elif cap >= 1e6:
        return f"${cap/1e6:,.2f}M"
    elif cap > 0:
        return f"${cap:,.0f}"
    return ""


@cli.command()
@click.option("--sector", "-s", default=None, help="Filter by sector")
@click.option("--industry", "-i", default=None, help="Filter by industry")
@click.option("--country", "-c", default=None, help="Filter by country")
@click.option("--style-box", default=None, help="Filter by style box (large_cap, mid_cap, small_cap)")
def search(sector: str | None, industry: str | None, country: str | None, style_box: str | None) -> None:
    """Search securities by criteria."""
    config = _get_config()
    conn = connect_db(config.db_path)
    q = SecMasterQuery(conn)

    df = q.search(sector=sector, industry=industry, country=country, style_box=style_box)

    if df.empty:
        console.print("[yellow]No securities found matching criteria.[/yellow]")
        conn.close()
        return

    table = Table(title=f"Securities ({len(df)} found)")
    for col in df.columns:
        justify = "right" if col == "market_cap" else "left"
        table.add_column(str(col), justify=justify)

    for _, row in df.head(50).iterrows():
        cells = []
        for col in df.columns:
            val = row[col]
            if col == "market_cap" and isinstance(val, (int, float)):
                cells.append(_format_market_cap(val))
            else:
                cells.append(str(val) if val else "")
        table.add_row(*cells)

    console.print(table)
    conn.close()


@cli.command()
def info() -> None:
    """Show database statistics."""
    config = _get_config()
    conn = connect_db(config.db_path)
    stats = get_db_stats(conn)

    table = Table(title="Security Master Database Info")
    table.add_column("Metric", style="bold")
    table.add_column("Value", justify="right")
    table.add_row("Securities", str(stats["securities"]))
    table.add_row("Sectors", str(stats["sectors"]))
    table.add_row("Countries", str(stats["countries"]))
    table.add_row("With ISIN", str(stats["with_isin"]))
    table.add_row("With FIGI", str(stats["with_figi"]))
    table.add_row("Database Path", str(config.db_path))

    console.print(table)
    conn.close()
