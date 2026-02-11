from __future__ import annotations

from datetime import date, datetime
from typing import Optional

import pandas as pd
import yfinance as yf

from app.schemas import Candle, QuoteResponse


class YFinanceError(Exception):
    pass


def _to_date(value: Optional[date]) -> Optional[str]:
    if value is None:
        return None
    return value.isoformat()


def get_daily_ohlcv(
    symbol: str,
    start: Optional[date] = None,
    end: Optional[date] = None,
) -> list[Candle]:
    try:
        ticker = yf.Ticker(symbol)
        history = ticker.history(
            interval="1d",
            start=_to_date(start),
            end=_to_date(end),
            auto_adjust=False,
        )
    except Exception as exc:  # pragma: no cover - yfinance raises various exceptions
        raise YFinanceError(f"yfinance request failed: {exc}") from exc

    if history.empty:
        return []

    history = history.reset_index()
    date_col = "Date" if "Date" in history.columns else "Datetime"

    candles: list[Candle] = []
    for _, row in history.iterrows():
        dt = row[date_col]
        if isinstance(dt, pd.Timestamp):
            dt = dt.to_pydatetime()
        if isinstance(dt, datetime):
            candle_date = dt.date()
        else:
            candle_date = date.fromisoformat(str(dt))

        candles.append(
            Candle(
                date=candle_date,
                open=float(row.get("Open", 0.0)),
                high=float(row.get("High", 0.0)),
                low=float(row.get("Low", 0.0)),
                close=float(row.get("Close", 0.0)),
                volume=int(row.get("Volume", 0)),
            )
        )

    return candles


def get_latest_quote(symbol: str) -> QuoteResponse:
    try:
        ticker = yf.Ticker(symbol)
        fast_info = getattr(ticker, "fast_info", None) or {}
    except Exception as exc:  # pragma: no cover
        raise YFinanceError(f"yfinance request failed: {exc}") from exc

    market_time = None
    last_time = fast_info.get("last_price_time") or fast_info.get("last_price_time")
    if isinstance(last_time, (int, float)):
        market_time = datetime.fromtimestamp(last_time)
    elif isinstance(last_time, datetime):
        market_time = last_time

    if not fast_info:
        try:
            info = ticker.info
        except Exception as exc:  # pragma: no cover
            raise YFinanceError(f"yfinance request failed: {exc}") from exc

        return QuoteResponse(
            symbol=symbol.upper(),
            price=info.get("regularMarketPrice"),
            previous_close=info.get("previousClose"),
            open=info.get("open"),
            day_high=info.get("dayHigh"),
            day_low=info.get("dayLow"),
            volume=info.get("volume"),
            currency=info.get("currency"),
            exchange=info.get("exchange"),
            market_time=None,
        )

    return QuoteResponse(
        symbol=symbol.upper(),
        price=fast_info.get("last_price"),
        previous_close=fast_info.get("previous_close"),
        open=fast_info.get("open"),
        day_high=fast_info.get("day_high"),
        day_low=fast_info.get("day_low"),
        volume=fast_info.get("volume"),
        currency=fast_info.get("currency"),
        exchange=fast_info.get("exchange"),
        market_time=market_time,
    )
