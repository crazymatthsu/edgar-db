"""Statement endpoints — income, balance, cashflow."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from ..dependencies import get_query
from ..schemas import StatementResponse

router = APIRouter(prefix="/api/statements", tags=["statements"])

_STATEMENT_METHODS = {
    "income": "get_income_statement",
    "balance": "get_balance_sheet",
    "cashflow": "get_cash_flow",
}


@router.get("/{ticker}/{statement_type}", response_model=StatementResponse)
def get_statement(
    ticker: str,
    statement_type: str,
    period: str = Query("annual", pattern="^(annual|quarterly)$"),
):
    if statement_type not in _STATEMENT_METHODS:
        raise HTTPException(status_code=400, detail=f"Invalid statement type: {statement_type}")

    query = get_query()
    try:
        method = getattr(query, _STATEMENT_METHODS[statement_type])
        df = method(ticker, period=period)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    if df.empty:
        return StatementResponse(
            ticker=ticker.upper(),
            statement=statement_type,
            period=period,
            columns=[],
            data=[],
        )

    columns = df.columns.tolist()
    # NaN → None (JSON null)
    data = df.where(df.notna(), None).to_dict(orient="records")

    return StatementResponse(
        ticker=ticker.upper(),
        statement=statement_type,
        period=period,
        columns=columns,
        data=data,
    )
