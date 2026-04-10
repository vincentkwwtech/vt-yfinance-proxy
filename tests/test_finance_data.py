"""Tests for all 8 finance-data endpoints with mocked yfinance."""
from __future__ import annotations

from datetime import datetime
from unittest.mock import MagicMock, PropertyMock, patch

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


# --------------- Fixtures / Helpers ---------------

def _make_info(valid: bool = True) -> dict:
    """Return a realistic info dict."""
    if not valid:
        return {}
    return {
        "shortName": "Apple Inc.",
        "longName": "Apple Inc.",
        "industry": "Consumer Electronics",
        "sector": "Technology",
        "marketCap": 3000000000000,
        "enterpriseValue": 3100000000000,
        "currency": "USD",
        "exchange": "NMS",
        "quoteType": "EQUITY",
        "website": "https://www.apple.com",
        "longBusinessSummary": "Apple designs and sells electronics.",
        "fullTimeEmployees": 164000,
        "address1": "One Apple Park Way",
        "city": "Cupertino",
        "state": "CA",
        "zip": "95014",
        "country": "United States",
        "phone": "408 996 1010",
        # Analyst fields
        "targetMeanPrice": 210.0,
        "targetHighPrice": 250.0,
        "targetLowPrice": 170.0,
        "targetMedianPrice": 215.0,
        "recommendationKey": "buy",
        "recommendationMean": 1.8,
        "numberOfAnalystOpinions": 40,
        # Financial metrics
        "trailingPE": 28.5,
        "forwardPE": 26.0,
        "priceToBook": 45.0,
        "returnOnEquity": 1.6,
        "returnOnAssets": 0.3,
        "debtToEquity": 180.0,
        "currentRatio": 1.0,
        "quickRatio": 0.9,
        "revenueGrowth": 0.05,
        "earningsGrowth": 0.1,
        "grossMargins": 0.46,
        "operatingMargins": 0.31,
        "profitMargins": 0.26,
        "dividendYield": 0.005,
        "payoutRatio": 0.15,
        "beta": 1.2,
        "trailingEps": 6.5,
        "forwardEps": 7.0,
        "bookValue": 4.0,
        "totalRevenue": 380000000000,
        "ebitda": 130000000000,
        "totalDebt": 120000000000,
        "totalCash": 60000000000,
        "freeCashflow": 100000000000,
        "operatingCashflow": 110000000000,
    }


def _make_dataframe(columns: list[str], rows: list[list]) -> pd.DataFrame:
    return pd.DataFrame(rows, columns=columns)


def _mock_ticker(valid: bool = True) -> MagicMock:
    """Build a fully mocked yfinance.Ticker object."""
    ticker = MagicMock()
    ticker.info = _make_info(valid)

    # major_holders
    ticker.major_holders = pd.DataFrame(
        [["5.00%", "Insiders"], ["60.00%", "Institutions"]],
        columns=["Value", "Breakdown"],
    )
    # institutional_holders
    ticker.institutional_holders = pd.DataFrame(
        [["Vanguard", 1200000000, 0.07, datetime(2024, 6, 30)]],
        columns=["Holder", "Shares", "% Out", "Date Reported"],
    )
    ticker.insider_transactions = pd.DataFrame()
    ticker.mutualfund_holders = pd.DataFrame()

    # Actions
    idx = pd.DatetimeIndex([datetime(2024, 5, 10), datetime(2024, 8, 12)])
    ticker.actions = pd.DataFrame(
        {"Dividends": [0.25, 0.25], "Stock Splits": [0.0, 0.0]}, index=idx
    )
    ticker.dividends = pd.Series([0.25, 0.25], index=idx, name="Dividends")
    ticker.splits = pd.Series([], dtype=float, name="Stock Splits")

    # Analyst
    ticker.upgrades_downgrades = pd.DataFrame(
        [["2024-01-15", "Morgan Stanley", "Overweight", "Equal-Weight", "Upgrade"]],
        columns=["Date", "Firm", "ToGrade", "FromGrade", "Action"],
    )
    ticker.recommendations = pd.DataFrame(
        [[1, 20, 10, 5, 2]],
        columns=["strongBuy", "buy", "hold", "sell", "strongSell"],
    )

    # Financial statements
    dates = pd.DatetimeIndex([datetime(2024, 9, 30)])
    ticker.income_stmt = pd.DataFrame(
        {"Total Revenue": [380000000000], "Net Income": [95000000000]},
        index=dates,
    ).T
    ticker.quarterly_income_stmt = pd.DataFrame(
        {"Total Revenue": [95000000000], "Net Income": [24000000000]},
        index=dates,
    ).T
    ticker.balance_sheet = pd.DataFrame(
        {"Total Assets": [350000000000], "Total Liabilities": [280000000000]},
        index=dates,
    ).T
    ticker.quarterly_balance_sheet = pd.DataFrame(
        {"Total Assets": [350000000000]},
        index=dates,
    ).T
    ticker.cashflow = pd.DataFrame(
        {"Operating Cash Flow": [110000000000]},
        index=dates,
    ).T
    ticker.quarterly_cashflow = pd.DataFrame(
        {"Operating Cash Flow": [28000000000]},
        index=dates,
    ).T

    # Options
    ticker.options = ("2024-12-20", "2025-01-17")
    calls_df = pd.DataFrame(
        [["AAPL241220C00100000", 100.0, 95.0, 96.0, 5.0, 1000, 500]],
        columns=["contractSymbol", "strike", "bid", "ask", "lastPrice", "volume", "openInterest"],
    )
    puts_df = pd.DataFrame(
        [["AAPL241220P00100000", 100.0, 3.0, 3.5, 3.2, 800, 300]],
        columns=["contractSymbol", "strike", "bid", "ask", "lastPrice", "volume", "openInterest"],
    )
    chain_mock = MagicMock()
    chain_mock.calls = calls_df
    chain_mock.puts = puts_df
    ticker.option_chain = MagicMock(return_value=chain_mock)

    # History (kline)
    kline_idx = pd.DatetimeIndex([datetime(2024, 1, 2), datetime(2024, 1, 3)])
    ticker.history = MagicMock(
        return_value=pd.DataFrame(
            {
                "Open": [185.0, 186.0],
                "High": [187.0, 188.0],
                "Low": [184.0, 185.0],
                "Close": [186.5, 187.5],
                "Volume": [50000000, 48000000],
            },
            index=kline_idx,
        )
    )

    return ticker


# --------------- Tests ---------------


class TestHealthEndpoint:
    def test_health(self):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}


class TestProfileEndpoint:
    @patch("app.services.finance_data_service._get_ticker")
    def test_valid_ticker(self, mock_get_ticker):
        mock_get_ticker.return_value = _mock_ticker(valid=True)
        resp = client.get("/finance-data/yfinance/profile?ticker=AAPL")
        assert resp.status_code == 200
        data = resp.json()
        assert data["ticker"] == "AAPL"
        assert data["name"] == "Apple Inc."
        assert data["industry"] == "Consumer Electronics"
        assert data["sector"] == "Technology"
        assert data["marketCap"] == 3000000000000
        assert data["website"] == "https://www.apple.com"
        assert data["fullTimeEmployees"] == 164000
        assert data["city"] == "Cupertino"

    @patch("app.services.finance_data_service._get_ticker")
    def test_invalid_ticker(self, mock_get_ticker):
        mock_get_ticker.return_value = _mock_ticker(valid=False)
        resp = client.get("/finance-data/yfinance/profile?ticker=INVALID")
        assert resp.status_code == 404

    def test_missing_ticker_param(self):
        resp = client.get("/finance-data/yfinance/profile")
        assert resp.status_code == 422  # validation error


class TestShareholdersEndpoint:
    @patch("app.services.finance_data_service._get_ticker")
    def test_valid(self, mock_get_ticker):
        mock_get_ticker.return_value = _mock_ticker()
        resp = client.get("/finance-data/yfinance/shareholders?ticker=AAPL")
        assert resp.status_code == 200
        data = resp.json()
        assert data["ticker"] == "AAPL"
        assert len(data["major_holders"]) == 2
        assert len(data["institutional_holders"]) == 1
        assert isinstance(data["insider_transactions"], list)
        assert isinstance(data["mutualfund_holders"], list)


class TestActionsEndpoint:
    @patch("app.services.finance_data_service._get_ticker")
    def test_valid(self, mock_get_ticker):
        mock_get_ticker.return_value = _mock_ticker()
        resp = client.get("/finance-data/yfinance/actions?ticker=AAPL")
        assert resp.status_code == 200
        data = resp.json()
        assert data["ticker"] == "AAPL"
        assert len(data["actions"]) == 2
        assert len(data["dividends"]) == 2
        assert data["splits"] == []  # no splits in mock


class TestAnalystEndpoint:
    @patch("app.services.finance_data_service._get_ticker")
    def test_valid(self, mock_get_ticker):
        mock_get_ticker.return_value = _mock_ticker()
        resp = client.get("/finance-data/yfinance/analyst?ticker=AAPL")
        assert resp.status_code == 200
        data = resp.json()
        assert data["ticker"] == "AAPL"
        assert data["target_mean_price"] == 210.0
        assert data["target_high_price"] == 250.0
        assert data["target_low_price"] == 170.0
        assert data["recommendation_key"] == "buy"
        assert data["number_of_analyst_opinions"] == 40
        assert len(data["upgrades_downgrades"]) == 1
        assert len(data["recommendations"]) == 1


class TestFinancialEndpoint:
    @patch("app.services.finance_data_service._get_ticker")
    def test_valid(self, mock_get_ticker):
        mock_get_ticker.return_value = _mock_ticker()
        resp = client.get("/finance-data/yfinance/financial?ticker=AAPL")
        assert resp.status_code == 200
        data = resp.json()
        assert data["ticker"] == "AAPL"
        assert len(data["income_statement"]) >= 1
        assert len(data["quarterly_income_statement"]) >= 1
        assert len(data["balance_sheet"]) >= 1
        assert len(data["quarterly_balance_sheet"]) >= 1
        assert len(data["cashflow"]) >= 1
        assert len(data["quarterly_cashflow"]) >= 1
        km = data["key_metrics"]
        assert km["trailingPE"] == 28.5
        assert km["returnOnEquity"] == 1.6
        assert km["debtToEquity"] == 180.0
        assert km["totalRevenue"] == 380000000000
        assert km["freeCashflow"] == 100000000000


class TestOptionChainEndpoint:
    @patch("app.services.finance_data_service._get_ticker")
    def test_without_expiration(self, mock_get_ticker):
        mock_get_ticker.return_value = _mock_ticker()
        resp = client.get("/finance-data/yfinance/optionchain?ticker=AAPL")
        assert resp.status_code == 200
        data = resp.json()
        assert data["ticker"] == "AAPL"
        assert "2024-12-20" in data["expirations"]
        assert "2025-01-17" in data["expirations"]
        assert data["calls"] == []
        assert data["puts"] == []

    @patch("app.services.finance_data_service._get_ticker")
    def test_with_expiration(self, mock_get_ticker):
        mock_get_ticker.return_value = _mock_ticker()
        resp = client.get("/finance-data/yfinance/optionchain?ticker=AAPL&expiration=2024-12-20")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["calls"]) == 1
        assert len(data["puts"]) == 1
        assert data["calls"][0]["strike"] == 100.0
        assert data["puts"][0]["strike"] == 100.0


class TestKlineEndpoint:
    @patch("app.services.finance_data_service._get_ticker")
    def test_default_params(self, mock_get_ticker):
        mock_get_ticker.return_value = _mock_ticker()
        resp = client.get("/finance-data/yfinance/kline?ticker=AAPL")
        assert resp.status_code == 200
        data = resp.json()
        assert data["ticker"] == "AAPL"
        assert data["period"] == "1y"
        assert data["interval"] == "1d"
        assert data["prepost"] is False
        assert len(data["data"]) == 2
        assert data["data"][0]["Open"] == 185.0

    @patch("app.services.finance_data_service._get_ticker")
    def test_custom_params(self, mock_get_ticker):
        mock_get_ticker.return_value = _mock_ticker()
        resp = client.get("/finance-data/yfinance/kline?ticker=AAPL&period=5d&interval=1m&prepost=true")
        assert resp.status_code == 200
        data = resp.json()
        assert data["period"] == "5d"
        assert data["interval"] == "1m"
        assert data["prepost"] is True

    @patch("app.services.finance_data_service._get_ticker")
    def test_invalid_period(self, mock_get_ticker):
        mock_get_ticker.return_value = _mock_ticker()
        resp = client.get("/finance-data/yfinance/kline?ticker=AAPL&period=999d")
        assert resp.status_code == 500
        assert "Invalid period" in resp.json()["detail"]

    @patch("app.services.finance_data_service._get_ticker")
    def test_invalid_interval(self, mock_get_ticker):
        mock_get_ticker.return_value = _mock_ticker()
        resp = client.get("/finance-data/yfinance/kline?ticker=AAPL&interval=999m")
        assert resp.status_code == 500
        assert "Invalid interval" in resp.json()["detail"]


class TestAllEndpoint:
    @patch("app.services.finance_data_service._get_ticker")
    def test_valid(self, mock_get_ticker):
        mock_get_ticker.return_value = _mock_ticker()
        resp = client.get("/finance-data/yfinance/all?ticker=AAPL")
        assert resp.status_code == 200
        data = resp.json()
        assert data["ticker"] == "AAPL"
        # All sub-sections present
        assert "profile" in data
        assert "shareholders" in data
        assert "actions" in data
        assert "analyst" in data
        assert "financial" in data
        assert "optionchain" in data
        assert "kline" in data
        # Spot-check sub-sections
        assert data["profile"]["name"] == "Apple Inc."
        assert data["analyst"]["target_mean_price"] == 210.0
        assert len(data["kline"]["data"]) == 2

    @patch("app.services.finance_data_service._get_ticker")
    def test_invalid_ticker(self, mock_get_ticker):
        mock_get_ticker.return_value = _mock_ticker(valid=False)
        resp = client.get("/finance-data/yfinance/all?ticker=INVALID")
        assert resp.status_code == 404


class TestProxyConfig:
    @patch.dict("os.environ", {"USE_PROXY": "true", "YFINANCE_PROXY": "http://myproxy:8080"})
    def test_proxy_enabled(self):
        from app.services.finance_data_service import _get_proxy
        assert _get_proxy() == "http://myproxy:8080"

    @patch.dict("os.environ", {"USE_PROXY": "false", "YFINANCE_PROXY": "http://myproxy:8080"})
    def test_proxy_disabled(self):
        from app.services.finance_data_service import _get_proxy
        assert _get_proxy() is None
