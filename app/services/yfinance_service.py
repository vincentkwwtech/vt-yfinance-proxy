from __future__ import annotations

from datetime import date, datetime
import logging
from typing import Optional

import pandas as pd
import yfinance as yf

from app.schemas import Candle, QuoteResponse


logger = logging.getLogger(__name__)


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
    symbol = symbol.upper()
    try:
        ticker = yf.Ticker(symbol)
        fast_info = getattr(ticker, "fast_info", None) or {}
    except Exception as exc:  # pragma: no cover
        raise YFinanceError(f"yfinance request failed: {exc}") from exc

    market_time = None
    last_time = (
        fast_info.get("last_price_time")
        or fast_info.get("last_trade_time")
        or fast_info.get("last_timestamp")
    )
    if isinstance(last_time, (int, float)):
        market_time = datetime.fromtimestamp(last_time)
    elif isinstance(last_time, datetime):
        market_time = last_time

    if fast_info:
        logger.info("quote fast_info keys=%s", sorted(fast_info.keys()))
    else:
        logger.warning("quote fast_info empty for %s", symbol)

    info = {}
    if not fast_info or fast_info.get("last_price") is None:
        try:
            info = ticker.info
            logger.info("quote info keys=%s", sorted(info.keys()))
        except Exception as exc:  # pragma: no cover
            logger.warning("quote info fetch failed for %s: %s", symbol, exc)

    price = fast_info.get("last_price") if fast_info else None
    if price is None:
        price = info.get("regularMarketPrice") or info.get("currentPrice")

    previous_close = fast_info.get("previous_close") if fast_info else None
    if previous_close is None:
        previous_close = info.get("previousClose")

    open_price = fast_info.get("open") if fast_info else None
    if open_price is None:
        open_price = info.get("open")

    day_high = fast_info.get("day_high") if fast_info else None
    if day_high is None:
        day_high = info.get("dayHigh")

    day_low = fast_info.get("day_low") if fast_info else None
    if day_low is None:
        day_low = info.get("dayLow")

    volume = fast_info.get("volume") if fast_info else None
    if volume is None:
        volume = info.get("volume")

    currency = fast_info.get("currency") if fast_info else None
    if currency is None:
        currency = info.get("currency")

    exchange = fast_info.get("exchange") if fast_info else None
    if exchange is None:
        exchange = info.get("exchange")

    if price is None:
        try:
            history = ticker.history(period="5d", interval="1d")
            if not history.empty:
                last_row = history.tail(1).iloc[0]
                price = float(last_row.get("Close", 0.0))
                logger.info("quote fallback price from history for %s", symbol)
        except Exception as exc:  # pragma: no cover
            logger.warning("quote history fallback failed for %s: %s", symbol, exc)

    if price is None:
        logger.warning("quote price still null for %s", symbol)

    return QuoteResponse(
        symbol=symbol,
        price=price,
        previous_close=previous_close,
        open=open_price,
        day_high=day_high,
        day_low=day_low,
        volume=volume,
        currency=currency,
        exchange=exchange,
        market_time=market_time,
    )
