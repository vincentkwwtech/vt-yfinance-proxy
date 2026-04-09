from __future__ import annotations

import logging
import os
from datetime import datetime
from typing import Any, Optional

import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)


def _get_proxy() -> Optional[str]:
    return os.getenv("YFINANCE_PROXY")


def _get_ticker(symbol: str) -> yf.Ticker:
    proxy = _get_proxy()
    ticker = yf.Ticker(symbol)
    if proxy:
        ticker.proxy = proxy
    return ticker


def _validate_ticker(ticker: yf.Ticker, symbol: str) -> None:
    """Raise 404-style error if ticker is invalid."""
    try:
        info = ticker.info
        if not info or info.get("trailingPegRatio") is None and info.get("shortName") is None:
            # yfinance returns minimal info for invalid tickers
            if not info.get("shortName") and not info.get("longName"):
                raise InvalidTickerError(f"Invalid ticker symbol: {symbol}")
    except InvalidTickerError:
        raise
    except Exception:
        pass  # Let downstream calls handle real errors


class InvalidTickerError(Exception):
    pass


class FinanceDataError(Exception):
    pass


def _safe_float(val: Any) -> Optional[float]:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


def _safe_int(val: Any) -> Optional[int]:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    try:
        return int(val)
    except (TypeError, ValueError):
        return None


def _safe_str(val: Any) -> Optional[str]:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    return str(val)


def _df_to_records(df: pd.DataFrame) -> list[dict]:
    """Convert a DataFrame to a list of dicts, handling NaN values."""
    if df is None or df.empty:
        return []
    df = df.reset_index()
    records = []
    for _, row in df.iterrows():
        record = {}
        for col in df.columns:
            val = row[col]
            if isinstance(val, pd.Timestamp):
                record[col] = val.isoformat()
            elif isinstance(val, datetime):
                record[col] = val.isoformat()
            elif isinstance(val, float) and pd.isna(val):
                record[col] = None
            else:
                record[col] = val
            # Convert numpy types to native Python types
            if hasattr(record[col], "item"):
                record[col] = record[col].item()
        records.append(record)
    return records


# ---------- 1. Profile ----------

def get_profile(symbol: str) -> dict:
    ticker = _get_ticker(symbol)
    try:
        info = ticker.info
    except Exception as exc:
        raise FinanceDataError(f"Failed to fetch profile for {symbol}: {exc}") from exc

    if not info or (not info.get("shortName") and not info.get("longName")):
        raise InvalidTickerError(f"Invalid ticker symbol: {symbol}")

    return {
        "ticker": symbol.upper(),
        "name": info.get("shortName") or info.get("longName"),
        "longName": info.get("longName"),
        "industry": info.get("industry"),
        "sector": info.get("sector"),
        "marketCap": _safe_int(info.get("marketCap")),
        "enterpriseValue": _safe_int(info.get("enterpriseValue")),
        "currency": info.get("currency"),
        "exchange": info.get("exchange"),
        "quoteType": info.get("quoteType"),
        "website": info.get("website"),
        "longBusinessSummary": info.get("longBusinessSummary"),
        "fullTimeEmployees": _safe_int(info.get("fullTimeEmployees")),
        "address1": info.get("address1"),
        "city": info.get("city"),
        "state": info.get("state"),
        "zip": info.get("zip"),
        "country": info.get("country"),
        "phone": info.get("phone"),
    }


# ---------- 2. Shareholders ----------

def get_shareholders(symbol: str) -> dict:
    ticker = _get_ticker(symbol)
    try:
        info = ticker.info
        if not info or (not info.get("shortName") and not info.get("longName")):
            raise InvalidTickerError(f"Invalid ticker symbol: {symbol}")

        major_holders = _df_to_records(getattr(ticker, "major_holders", None))
        institutional_holders = _df_to_records(getattr(ticker, "institutional_holders", None))
        insider_transactions = _df_to_records(getattr(ticker, "insider_transactions", None))
        mutualfund_holders = _df_to_records(getattr(ticker, "mutualfund_holders", None))
    except InvalidTickerError:
        raise
    except Exception as exc:
        raise FinanceDataError(f"Failed to fetch shareholders for {symbol}: {exc}") from exc

    return {
        "ticker": symbol.upper(),
        "major_holders": major_holders,
        "institutional_holders": institutional_holders,
        "insider_transactions": insider_transactions,
        "mutualfund_holders": mutualfund_holders,
    }


# ---------- 3. Actions ----------

def get_actions(symbol: str) -> dict:
    ticker = _get_ticker(symbol)
    try:
        info = ticker.info
        if not info or (not info.get("shortName") and not info.get("longName")):
            raise InvalidTickerError(f"Invalid ticker symbol: {symbol}")

        actions = _df_to_records(ticker.actions)
        dividends = _df_to_records(ticker.dividends.to_frame() if not ticker.dividends.empty else pd.DataFrame())
        splits = _df_to_records(ticker.splits.to_frame() if not ticker.splits.empty else pd.DataFrame())
    except InvalidTickerError:
        raise
    except Exception as exc:
        raise FinanceDataError(f"Failed to fetch actions for {symbol}: {exc}") from exc

    return {
        "ticker": symbol.upper(),
        "actions": actions,
        "dividends": dividends,
        "splits": splits,
    }


# ---------- 4. Analyst ----------

def get_analyst(symbol: str) -> dict:
    ticker = _get_ticker(symbol)
    try:
        info = ticker.info
        if not info or (not info.get("shortName") and not info.get("longName")):
            raise InvalidTickerError(f"Invalid ticker symbol: {symbol}")

        upgrades_downgrades = _df_to_records(getattr(ticker, "upgrades_downgrades", None))
        recommendations = _df_to_records(getattr(ticker, "recommendations", None))
    except InvalidTickerError:
        raise
    except Exception as exc:
        raise FinanceDataError(f"Failed to fetch analyst data for {symbol}: {exc}") from exc

    return {
        "ticker": symbol.upper(),
        "upgrades_downgrades": upgrades_downgrades,
        "recommendations": recommendations,
        "target_mean_price": _safe_float(info.get("targetMeanPrice")),
        "target_high_price": _safe_float(info.get("targetHighPrice")),
        "target_low_price": _safe_float(info.get("targetLowPrice")),
        "target_median_price": _safe_float(info.get("targetMedianPrice")),
        "recommendation_key": info.get("recommendationKey"),
        "recommendation_mean": _safe_float(info.get("recommendationMean")),
        "number_of_analyst_opinions": _safe_int(info.get("numberOfAnalystOpinions")),
    }


# ---------- 5. Financial ----------

def get_financial(symbol: str) -> dict:
    ticker = _get_ticker(symbol)
    try:
        info = ticker.info
        if not info or (not info.get("shortName") and not info.get("longName")):
            raise InvalidTickerError(f"Invalid ticker symbol: {symbol}")

        income_stmt = _df_to_records(ticker.income_stmt.T if not ticker.income_stmt.empty else pd.DataFrame())
        quarterly_income_stmt = _df_to_records(ticker.quarterly_income_stmt.T if not ticker.quarterly_income_stmt.empty else pd.DataFrame())
        balance_sheet = _df_to_records(ticker.balance_sheet.T if not ticker.balance_sheet.empty else pd.DataFrame())
        quarterly_balance_sheet = _df_to_records(ticker.quarterly_balance_sheet.T if not ticker.quarterly_balance_sheet.empty else pd.DataFrame())
        cashflow = _df_to_records(ticker.cashflow.T if not ticker.cashflow.empty else pd.DataFrame())
        quarterly_cashflow = _df_to_records(ticker.quarterly_cashflow.T if not ticker.quarterly_cashflow.empty else pd.DataFrame())
    except InvalidTickerError:
        raise
    except Exception as exc:
        raise FinanceDataError(f"Failed to fetch financial data for {symbol}: {exc}") from exc

    key_metrics = {
        "trailingPE": _safe_float(info.get("trailingPE")),
        "forwardPE": _safe_float(info.get("forwardPE")),
        "priceToBook": _safe_float(info.get("priceToBook")),
        "returnOnEquity": _safe_float(info.get("returnOnEquity")),
        "returnOnAssets": _safe_float(info.get("returnOnAssets")),
        "debtToEquity": _safe_float(info.get("debtToEquity")),
        "currentRatio": _safe_float(info.get("currentRatio")),
        "quickRatio": _safe_float(info.get("quickRatio")),
        "revenueGrowth": _safe_float(info.get("revenueGrowth")),
        "earningsGrowth": _safe_float(info.get("earningsGrowth")),
        "grossMargins": _safe_float(info.get("grossMargins")),
        "operatingMargins": _safe_float(info.get("operatingMargins")),
        "profitMargins": _safe_float(info.get("profitMargins")),
        "dividendYield": _safe_float(info.get("dividendYield")),
        "payoutRatio": _safe_float(info.get("payoutRatio")),
        "beta": _safe_float(info.get("beta")),
        "trailingEps": _safe_float(info.get("trailingEps")),
        "forwardEps": _safe_float(info.get("forwardEps")),
        "bookValue": _safe_float(info.get("bookValue")),
        "totalRevenue": _safe_int(info.get("totalRevenue")),
        "ebitda": _safe_int(info.get("ebitda")),
        "totalDebt": _safe_int(info.get("totalDebt")),
        "totalCash": _safe_int(info.get("totalCash")),
        "freeCashflow": _safe_int(info.get("freeCashflow")),
        "operatingCashflow": _safe_int(info.get("operatingCashflow")),
    }

    return {
        "ticker": symbol.upper(),
        "income_statement": income_stmt,
        "quarterly_income_statement": quarterly_income_stmt,
        "balance_sheet": balance_sheet,
        "quarterly_balance_sheet": quarterly_balance_sheet,
        "cashflow": cashflow,
        "quarterly_cashflow": quarterly_cashflow,
        "key_metrics": key_metrics,
    }


# ---------- 6. Option Chain ----------

def get_optionchain(symbol: str, expiration: Optional[str] = None) -> dict:
    ticker = _get_ticker(symbol)
    try:
        info = ticker.info
        if not info or (not info.get("shortName") and not info.get("longName")):
            raise InvalidTickerError(f"Invalid ticker symbol: {symbol}")

        expirations = list(ticker.options) if ticker.options else []
    except InvalidTickerError:
        raise
    except Exception as exc:
        raise FinanceDataError(f"Failed to fetch option chain for {symbol}: {exc}") from exc

    result: dict[str, Any] = {
        "ticker": symbol.upper(),
        "expirations": expirations,
    }

    if expiration:
        try:
            chain = ticker.option_chain(expiration)
            result["calls"] = _df_to_records(chain.calls)
            result["puts"] = _df_to_records(chain.puts)
        except Exception as exc:
            raise FinanceDataError(f"Failed to fetch option chain for {symbol} at {expiration}: {exc}") from exc
    else:
        result["calls"] = []
        result["puts"] = []

    return result


# ---------- 7. Kline ----------

VALID_PERIODS = {"1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"}
VALID_INTERVALS = {"1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h", "1d", "5d", "1wk", "1mo", "3mo"}


def get_kline(
    symbol: str,
    period: str = "1y",
    interval: str = "1d",
    prepost: bool = False,
) -> dict:
    if period not in VALID_PERIODS:
        raise FinanceDataError(f"Invalid period: {period}. Valid: {sorted(VALID_PERIODS)}")
    if interval not in VALID_INTERVALS:
        raise FinanceDataError(f"Invalid interval: {interval}. Valid: {sorted(VALID_INTERVALS)}")

    ticker = _get_ticker(symbol)
    try:
        info = ticker.info
        if not info or (not info.get("shortName") and not info.get("longName")):
            raise InvalidTickerError(f"Invalid ticker symbol: {symbol}")

        proxy = _get_proxy()
        history = ticker.history(
            period=period,
            interval=interval,
            prepost=prepost,
            auto_adjust=False,
            proxy=proxy,
        )
    except InvalidTickerError:
        raise
    except Exception as exc:
        raise FinanceDataError(f"Failed to fetch kline for {symbol}: {exc}") from exc

    records = _df_to_records(history)

    return {
        "ticker": symbol.upper(),
        "period": period,
        "interval": interval,
        "prepost": prepost,
        "data": records,
    }


# ---------- 8. All ----------

def get_all(symbol: str) -> dict:
    return {
        "ticker": symbol.upper(),
        "profile": get_profile(symbol),
        "shareholders": get_shareholders(symbol),
        "actions": get_actions(symbol),
        "analyst": get_analyst(symbol),
        "financial": get_financial(symbol),
        "optionchain": get_optionchain(symbol),
        "kline": get_kline(symbol, period="1y", interval="1d"),
    }
