from __future__ import annotations

from datetime import date

from fastapi import APIRouter, HTTPException, Query

from app.schemas import DailySeriesResponse, QuoteResponse
from app.services.yfinance_service import YFinanceError, get_daily_ohlcv, get_latest_quote


router = APIRouter()


@router.get("/stocks/{symbol}/daily", response_model=DailySeriesResponse)
def stock_daily(
    symbol: str,
    start: date | None = Query(default=None, description="Start date, YYYY-MM-DD"),
    end: date | None = Query(default=None, description="End date, YYYY-MM-DD"),
) -> DailySeriesResponse:
    try:
        candles = get_daily_ohlcv(symbol, start=start, end=end)
    except YFinanceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return DailySeriesResponse(symbol=symbol.upper(), candles=candles)


@router.get("/vix/daily", response_model=DailySeriesResponse)
def vix_daily(
    start: date | None = Query(default=None, description="Start date, YYYY-MM-DD"),
    end: date | None = Query(default=None, description="End date, YYYY-MM-DD"),
) -> DailySeriesResponse:
    symbol = "^VIX"
    try:
        candles = get_daily_ohlcv(symbol, start=start, end=end)
    except YFinanceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return DailySeriesResponse(symbol=symbol, candles=candles)


@router.get("/stocks/{symbol}/quote", response_model=QuoteResponse)
def stock_quote(symbol: str) -> QuoteResponse:
    try:
        return get_latest_quote(symbol)
    except YFinanceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
