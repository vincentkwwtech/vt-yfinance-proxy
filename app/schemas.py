from __future__ import annotations

from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel


class Candle(BaseModel):
    date: date
    open: float
    high: float
    low: float
    close: float
    volume: int


class DailySeriesResponse(BaseModel):
    symbol: str
    candles: List[Candle]


class QuoteResponse(BaseModel):
    symbol: str
    price: Optional[float] = None
    previous_close: Optional[float] = None
    open: Optional[float] = None
    day_high: Optional[float] = None
    day_low: Optional[float] = None
    volume: Optional[int] = None
    currency: Optional[str] = None
    exchange: Optional[str] = None
    market_time: Optional[datetime] = None
