"""Download endpoint — triggers SEC data download for a ticker."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from edgar_db.client import EdgarClient
from edgar_db.downloader import download_company

from ..dependencies import get_config, get_conn
from ..schemas import DownloadResponse

router = APIRouter(prefix="/api", tags=["download"])


@router.post("/download/{ticker}", response_model=DownloadResponse)
def download(
    ticker: str,
    force: bool = Query(False),
):
    conn = get_conn()
    config = get_config()

    try:
        with EdgarClient(config) as client:
            count = download_company(conn, client, ticker, force=force)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    status = "downloaded" if count > 0 else "already_current"
    return DownloadResponse(
        ticker=ticker.upper(),
        status=status,
        facts_count=count,
    )
