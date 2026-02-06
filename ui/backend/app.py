"""FastAPI application — EDGAR financial data REST API."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .dependencies import close_conn, get_conn
from .routes import download, health, metrics, statements


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure DB connection is ready
    get_conn()
    yield
    # Shutdown: close DB connection
    close_conn()


app = FastAPI(
    title="EDGAR Financial Database API",
    description="REST API for SEC EDGAR financial data",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(download.router)
app.include_router(statements.router)
app.include_router(metrics.router)
