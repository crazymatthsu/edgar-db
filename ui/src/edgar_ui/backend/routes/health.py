"""Health and stats endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from edgar_db.db import get_db_stats

from ..dependencies import get_conn, get_db_path
from ..schemas import HealthResponse, StatsResponse

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health():
    return HealthResponse(status="ok", db_path=str(get_db_path()))


@router.get("/stats", response_model=StatsResponse)
def stats():
    conn = get_conn()
    s = get_db_stats(conn)
    return StatsResponse(**s)
