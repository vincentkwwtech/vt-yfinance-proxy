from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.services.finance_data_service import (
    FinanceDataError,
    InvalidTickerError,
    get_actions,
    get_all,
    get_analyst,
    get_financial,
    get_kline,
    get_optionchain,
    get_profile,
    get_shareholders,
)

router = APIRouter()


def _handle_error(exc: Exception) -> None:
    if isinstance(exc, InvalidTickerError):
        raise HTTPException(status_code=404, detail=str(exc))
    raise HTTPException(status_code=500, detail=str(exc))


@router.get("/profile")
def profile(ticker: str = Query(..., description="Stock ticker symbol, e.g. AAPL")) -> dict:
    try:
        return get_profile(ticker)
    except (InvalidTickerError, FinanceDataError) as exc:
        _handle_error(exc)


@router.get("/shareholders")
def shareholders(ticker: str = Query(..., description="Stock ticker symbol, e.g. AAPL")) -> dict:
    try:
        return get_shareholders(ticker)
    except (InvalidTickerError, FinanceDataError) as exc:
        _handle_error(exc)


@router.get("/actions")
def actions(ticker: str = Query(..., description="Stock ticker symbol, e.g. AAPL")) -> dict:
    try:
        return get_actions(ticker)
    except (InvalidTickerError, FinanceDataError) as exc:
        _handle_error(exc)


@router.get("/analyst")
def analyst(ticker: str = Query(..., description="Stock ticker symbol, e.g. AAPL")) -> dict:
    try:
        return get_analyst(ticker)
    except (InvalidTickerError, FinanceDataError) as exc:
        _handle_error(exc)


@router.get("/financial")
def financial(ticker: str = Query(..., description="Stock ticker symbol, e.g. AAPL")) -> dict:
    try:
        return get_financial(ticker)
    except (InvalidTickerError, FinanceDataError) as exc:
        _handle_error(exc)


@router.get("/optionchain")
def optionchain(
    ticker: str = Query(..., description="Stock ticker symbol, e.g. AAPL"),
    expiration: str | None = Query(default=None, description="Option expiration date, e.g. 2024-12-20"),
) -> dict:
    try:
        return get_optionchain(ticker, expiration=expiration)
    except (InvalidTickerError, FinanceDataError) as exc:
        _handle_error(exc)


@router.get("/kline")
def kline(
    ticker: str = Query(..., description="Stock ticker symbol, e.g. AAPL"),
    period: str = Query(default="1y", description="Time period: 1d,5d,1mo,3mo,6mo,1y,2y,5y,10y,ytd,max"),
    interval: str = Query(default="1d", description="Kline interval: 1m,2m,5m,15m,30m,60m,90m,1h,1d,5d,1wk,1mo,3mo"),
    prepost: bool = Query(default=False, description="Include pre/post market data"),
) -> dict:
    try:
        return get_kline(ticker, period=period, interval=interval, prepost=prepost)
    except (InvalidTickerError, FinanceDataError) as exc:
        _handle_error(exc)


@router.get("/all")
def all_data(ticker: str = Query(..., description="Stock ticker symbol, e.g. AAPL")) -> dict:
    try:
        return get_all(ticker)
    except (InvalidTickerError, FinanceDataError) as exc:
        _handle_error(exc)
