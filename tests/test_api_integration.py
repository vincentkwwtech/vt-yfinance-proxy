"""
VT YFinance Proxy 接口功能测试

使用 mock 隔离外部依赖（Yahoo Finance），
对 Docker Compose 部署的服务所有端点进行全面测试。
"""

import os
from datetime import datetime
from unittest.mock import patch, MagicMock

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


# ======================== mock 工具 ========================

def _mock_info(valid=True):
    if not valid:
        return {}
    return {
        "shortName": "Apple Inc.",
        "longName": "Apple Inc.",
        "industry": "Consumer Electronics",
        "sector": "Technology",
        "marketCap": 2800000000000,
        "enterpriseValue": 2900000000000,
        "currency": "USD",
        "exchange": "NMS",
        "quoteType": "EQUITY",
        "website": "https://www.apple.com",
        "longBusinessSummary": "Apple Inc. designs, manufactures, and markets smartphones.",
        "fullTimeEmployees": 164000,
        "address1": "One Apple Park Way",
        "city": "Cupertino",
        "state": "CA",
        "zip": "95014",
        "country": "United States",
        "phone": "408-996-1010",
        "targetMeanPrice": 210.5,
        "targetHighPrice": 250.0,
        "targetLowPrice": 180.0,
        "targetMedianPrice": 212.0,
        "recommendationKey": "buy",
        "recommendationMean": 1.8,
        "numberOfAnalystOpinions": 42,
        "trailingPE": 28.5,
        "forwardPE": 26.1,
        "priceToBook": 45.2,
        "returnOnEquity": 1.56,
        "returnOnAssets": 0.28,
        "debtToEquity": 176.3,
        "profitMargins": 0.26,
        "operatingMargins": 0.30,
        "grossMargins": 0.46,
        "revenueGrowth": 0.08,
        "earningsGrowth": 0.12,
        "freeCashflow": 110000000000,
        "operatingCashflow": 120000000000,
        "totalDebt": 108000000000,
        "totalCash": 62000000000,
        "totalRevenue": 383000000000,
        "ebitda": 130000000000,
        "trailingEps": 6.42,
        "forwardEps": 7.10,
        "currentPrice": 185.92,
        "previousClose": 184.25,
        "open": 185.50,
        "dayHigh": 186.20,
        "dayLow": 184.30,
        "volume": 45000000,
    }


def _build_mock_ticker(valid=True):
    """构建完整 mock yfinance.Ticker"""
    ticker = MagicMock()
    ticker.info = _mock_info(valid)

    # shareholders
    ticker.major_holders = pd.DataFrame(
        [["7.5%", "Insiders"], ["60.1%", "Institutions"]],
        columns=["Value", "Holder"],
    )
    ticker.institutional_holders = pd.DataFrame(
        [["Vanguard", 1300000000, 260000000000, 8.5, pd.Timestamp("2024-01-01")]],
        columns=["Holder", "Shares", "Value", "% Out", "Date Reported"],
    )
    ticker.insider_transactions = pd.DataFrame(
        [["Tim Cook", "Sale", pd.Timestamp("2024-02-01"), 50000, 185.0]],
        columns=["Insider", "Transaction", "Date", "Shares", "Value"],
    )
    ticker.mutualfund_holders = pd.DataFrame(
        [["Vanguard 500", 500000000, 100000000000, 3.2, pd.Timestamp("2024-01-01")]],
        columns=["Holder", "Shares", "Value", "% Out", "Date Reported"],
    )

    # actions
    ticker.actions = pd.DataFrame(
        [[0.24, 0.0]], columns=["Dividends", "Stock Splits"],
        index=pd.DatetimeIndex([pd.Timestamp("2024-02-09")]),
    )
    ticker.dividends = pd.Series(
        [0.24], index=pd.DatetimeIndex([pd.Timestamp("2024-02-09")]), name="Dividends",
    )
    ticker.splits = pd.Series(
        [4.0], index=pd.DatetimeIndex([pd.Timestamp("2020-08-31")]), name="Stock Splits",
    )

    # analyst
    ticker.upgrades_downgrades = pd.DataFrame(
        [["Morgan Stanley", "Overweight", "Equal-Weight", pd.Timestamp("2024-03-01")]],
        columns=["Firm", "ToGrade", "FromGrade", "GradeDate"],
    )
    ticker.recommendations = pd.DataFrame(
        [["Morgan Stanley", "Buy", pd.Timestamp("2024-03-01")]],
        columns=["Firm", "To Grade", "Date"],
    )

    # financials
    stmt_cols = [pd.Timestamp("2024-01-01"), pd.Timestamp("2023-01-01")]
    ticker.income_stmt = pd.DataFrame(
        {"TotalRevenue": [383e9, 365e9], "NetIncome": [97e9, 94e9]}, index=stmt_cols,
    ).T
    ticker.quarterly_income_stmt = pd.DataFrame(
        {"TotalRevenue": [96e9, 91e9]}, index=stmt_cols,
    ).T
    ticker.balance_sheet = pd.DataFrame(
        {"TotalAssets": [350e9, 340e9]}, index=stmt_cols,
    ).T
    ticker.quarterly_balance_sheet = pd.DataFrame(
        {"TotalAssets": [350e9, 340e9]}, index=stmt_cols,
    ).T
    ticker.cashflow = pd.DataFrame(
        {"OperatingCashFlow": [120e9, 115e9]}, index=stmt_cols,
    ).T
    ticker.quarterly_cashflow = pd.DataFrame(
        {"OperatingCashFlow": [30e9, 28e9]}, index=stmt_cols,
    ).T

    # options
    ticker.options = ("2024-03-15", "2024-04-19", "2024-05-17")
    calls_df = pd.DataFrame({
        "strike": [170.0, 175.0],
        "lastPrice": [15.5, 10.5],
        "bid": [15.3, 10.3],
        "ask": [15.7, 10.7],
        "volume": [1200, 800],
        "openInterest": [5600, 3200],
        "impliedVolatility": [0.25, 0.22],
    })
    puts_df = pd.DataFrame({
        "strike": [170.0, 165.0],
        "lastPrice": [2.5, 4.5],
    })
    oc = MagicMock()
    oc.calls = calls_df
    oc.puts = puts_df
    ticker.option_chain = MagicMock(return_value=oc)

    # history (kline)
    hist_index = pd.DatetimeIndex([
        pd.Timestamp("2024-01-02"), pd.Timestamp("2024-01-03"),
        pd.Timestamp("2024-01-04"),
    ])
    ticker.history = MagicMock(return_value=pd.DataFrame({
        "Open": [185.5, 186.0, 184.8],
        "High": [186.2, 187.1, 186.5],
        "Low": [184.3, 185.2, 183.9],
        "Close": [185.8, 186.5, 185.2],
        "Volume": [45000000, 42000000, 48000000],
    }, index=hist_index))

    return ticker


# ======================== 测试用例 ========================

MOCK_FDS = "app.services.finance_data_service._get_ticker"


class TestHealthEndpoint:
    """测试 1: 健康检查 GET /health"""

    def test_returns_200_ok(self):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}


class TestParameterValidation:
    """测试 2: 参数校验 — 所有 v2 端点缺少 ticker 返回 422"""

    @pytest.mark.parametrize("endpoint", [
        "/finance-data/yfinance/profile",
        "/finance-data/yfinance/shareholders",
        "/finance-data/yfinance/actions",
        "/finance-data/yfinance/analyst",
        "/finance-data/yfinance/financial",
        "/finance-data/yfinance/optionchain",
        "/finance-data/yfinance/kline",
        "/finance-data/yfinance/all",
    ])
    def test_missing_ticker_returns_422(self, endpoint):
        resp = client.get(endpoint)
        assert resp.status_code == 422


class TestProfileEndpoint:
    """测试 3: 公司概况 GET /finance-data/yfinance/profile"""

    @patch(MOCK_FDS)
    def test_valid_ticker(self, mock_gt):
        mock_gt.return_value = _build_mock_ticker()
        resp = client.get("/finance-data/yfinance/profile?ticker=AAPL")
        assert resp.status_code == 200
        data = resp.json()
        assert data["ticker"] == "AAPL"
        assert data["name"] == "Apple Inc."
        assert data["sector"] == "Technology"
        assert data["industry"] == "Consumer Electronics"
        assert data["marketCap"] == 2800000000000
        assert data["exchange"] == "NMS"
        assert data["website"] == "https://www.apple.com"
        assert data["fullTimeEmployees"] == 164000
        assert data["city"] == "Cupertino"
        assert data["country"] == "United States"

    @patch(MOCK_FDS)
    def test_invalid_ticker_returns_404(self, mock_gt):
        mock_gt.return_value = _build_mock_ticker(valid=False)
        resp = client.get("/finance-data/yfinance/profile?ticker=INVALID")
        assert resp.status_code == 404


class TestShareholdersEndpoint:
    """测试 4: 股东信息 GET /finance-data/yfinance/shareholders"""

    @patch(MOCK_FDS)
    def test_valid(self, mock_gt):
        mock_gt.return_value = _build_mock_ticker()
        resp = client.get("/finance-data/yfinance/shareholders?ticker=AAPL")
        assert resp.status_code == 200
        data = resp.json()
        assert "major_holders" in data
        assert "institutional_holders" in data
        assert "insider_transactions" in data
        assert "mutualfund_holders" in data
        assert len(data["major_holders"]) >= 1


class TestActionsEndpoint:
    """测试 5: 公司行为 GET /finance-data/yfinance/actions"""

    @patch(MOCK_FDS)
    def test_valid(self, mock_gt):
        mock_gt.return_value = _build_mock_ticker()
        resp = client.get("/finance-data/yfinance/actions?ticker=AAPL")
        assert resp.status_code == 200
        data = resp.json()
        assert "actions" in data
        assert "dividends" in data
        assert "splits" in data


class TestAnalystEndpoint:
    """测试 6: 分析师评级 GET /finance-data/yfinance/analyst"""

    @patch(MOCK_FDS)
    def test_valid(self, mock_gt):
        mock_gt.return_value = _build_mock_ticker()
        resp = client.get("/finance-data/yfinance/analyst?ticker=AAPL")
        assert resp.status_code == 200
        data = resp.json()
        assert data["target_mean_price"] == 210.5
        assert data["target_high_price"] == 250.0
        assert data["target_low_price"] == 180.0
        assert data["target_median_price"] == 212.0
        assert data["recommendation_key"] == "buy"
        assert data["recommendation_mean"] == 1.8
        assert data["number_of_analyst_opinions"] == 42


class TestFinancialEndpoint:
    """测试 7: 财务数据 GET /finance-data/yfinance/financial"""

    @patch(MOCK_FDS)
    def test_valid(self, mock_gt):
        mock_gt.return_value = _build_mock_ticker()
        resp = client.get("/finance-data/yfinance/financial?ticker=AAPL")
        assert resp.status_code == 200
        data = resp.json()
        for key in ["income_statement", "quarterly_income_statement",
                     "balance_sheet", "quarterly_balance_sheet",
                     "cashflow", "quarterly_cashflow", "key_metrics"]:
            assert key in data, f"缺少字段: {key}"
        km = data["key_metrics"]
        assert km["trailingPE"] == 28.5
        assert km["forwardPE"] == 26.1
        assert km["profitMargins"] == 0.26
        assert km["returnOnEquity"] == 1.56


class TestOptionChainEndpoint:
    """测试 8: 期权链 GET /finance-data/yfinance/optionchain"""

    @patch(MOCK_FDS)
    def test_without_expiration_returns_expirations(self, mock_gt):
        mock_gt.return_value = _build_mock_ticker()
        resp = client.get("/finance-data/yfinance/optionchain?ticker=AAPL")
        assert resp.status_code == 200
        data = resp.json()
        assert "expirations" in data
        assert len(data["expirations"]) == 3
        assert "2024-03-15" in data["expirations"]

    @patch(MOCK_FDS)
    def test_with_expiration_returns_calls_puts(self, mock_gt):
        mock_gt.return_value = _build_mock_ticker()
        resp = client.get("/finance-data/yfinance/optionchain?ticker=AAPL&expiration=2024-03-15")
        assert resp.status_code == 200
        data = resp.json()
        assert "calls" in data
        assert "puts" in data
        assert len(data["calls"]) == 2
        assert data["calls"][0]["strike"] == 170.0


class TestKlineEndpoint:
    """测试 9: K线数据 GET /finance-data/yfinance/kline"""

    @patch(MOCK_FDS)
    def test_default_params(self, mock_gt):
        mock_gt.return_value = _build_mock_ticker()
        resp = client.get("/finance-data/yfinance/kline?ticker=AAPL")
        assert resp.status_code == 200
        data = resp.json()
        assert data["ticker"] == "AAPL"
        assert data["period"] == "1y"
        assert data["interval"] == "1d"
        assert data["prepost"] is False
        assert len(data["data"]) == 3
        bar = data["data"][0]
        assert "Open" in bar or "open" in bar

    @patch(MOCK_FDS)
    def test_custom_params(self, mock_gt):
        mock_gt.return_value = _build_mock_ticker()
        resp = client.get("/finance-data/yfinance/kline?ticker=AAPL&period=3mo&interval=1wk&prepost=true")
        assert resp.status_code == 200
        data = resp.json()
        assert data["period"] == "3mo"
        assert data["interval"] == "1wk"
        assert data["prepost"] is True

    @patch(MOCK_FDS)
    def test_invalid_period_returns_500(self, mock_gt):
        mock_gt.return_value = _build_mock_ticker()
        resp = client.get("/finance-data/yfinance/kline?ticker=AAPL&period=99d")
        assert resp.status_code == 500

    @patch(MOCK_FDS)
    def test_invalid_interval_returns_500(self, mock_gt):
        mock_gt.return_value = _build_mock_ticker()
        resp = client.get("/finance-data/yfinance/kline?ticker=AAPL&interval=99m")
        assert resp.status_code == 500


class TestAllEndpoint:
    """测试 10: 全量数据 GET /finance-data/yfinance/all"""

    @patch(MOCK_FDS)
    def test_valid_returns_all_modules(self, mock_gt):
        mock_gt.return_value = _build_mock_ticker()
        resp = client.get("/finance-data/yfinance/all?ticker=AAPL")
        assert resp.status_code == 200
        data = resp.json()
        for key in ["profile", "shareholders", "actions", "analyst",
                     "financial", "optionchain", "kline"]:
            assert key in data, f"全量数据缺少: {key}"
        assert data["profile"]["name"] == "Apple Inc."
        assert data["analyst"]["recommendation_key"] == "buy"

    @patch(MOCK_FDS)
    def test_invalid_ticker_returns_404(self, mock_gt):
        mock_gt.return_value = _build_mock_ticker(valid=False)
        resp = client.get("/finance-data/yfinance/all?ticker=INVALIDXYZ")
        assert resp.status_code == 404


class TestLegacyStockDaily:
    """测试 11: Legacy 股票日线 GET /api/v1/stocks/{symbol}/daily"""

    @patch("app.routers.market.get_daily_ohlcv")
    def test_returns_candles(self, mock_fn):
        from app.schemas import Candle
        from datetime import date as dt_date
        mock_fn.return_value = [
            Candle(date=dt_date(2024, 1, 2), open=185.5, high=186.2, low=184.3, close=185.8, volume=45000000),
        ]
        resp = client.get("/api/v1/stocks/AAPL/daily")
        assert resp.status_code == 200
        data = resp.json()
        assert data["symbol"] == "AAPL"
        assert len(data["candles"]) == 1
        assert data["candles"][0]["close"] == 185.8
        assert data["candles"][0]["date"] == "2024-01-02"

    @patch("app.routers.market.get_daily_ohlcv")
    def test_with_date_range(self, mock_fn):
        from app.schemas import Candle
        from datetime import date as dt_date
        mock_fn.return_value = [
            Candle(date=dt_date(2024, 1, 2), open=185.5, high=186.2, low=184.3, close=185.8, volume=45000000),
            Candle(date=dt_date(2024, 1, 3), open=186.0, high=187.1, low=185.2, close=186.5, volume=42000000),
        ]
        resp = client.get("/api/v1/stocks/AAPL/daily?start=2024-01-01&end=2024-02-01")
        assert resp.status_code == 200
        assert len(resp.json()["candles"]) == 2


class TestLegacyVixDaily:
    """测试 12: Legacy VIX 日线 GET /api/v1/vix/daily"""

    @patch("app.routers.market.get_daily_ohlcv")
    def test_returns_vix_data(self, mock_fn):
        from app.schemas import Candle
        from datetime import date as dt_date
        mock_fn.return_value = [
            Candle(date=dt_date(2024, 1, 2), open=14.5, high=15.2, low=13.8, close=14.9, volume=0),
        ]
        resp = client.get("/api/v1/vix/daily")
        assert resp.status_code == 200
        data = resp.json()
        assert data["symbol"] == "^VIX"
        assert data["candles"][0]["close"] == 14.9


class TestLegacyStockQuote:
    """测试 13: Legacy 实时报价 GET /api/v1/stocks/{symbol}/quote"""

    @patch("app.routers.market.get_latest_quote")
    def test_returns_quote(self, mock_fn):
        from app.schemas import QuoteResponse
        mock_fn.return_value = QuoteResponse(
            symbol="AAPL",
            price=185.92,
            previous_close=184.25,
            open=185.50,
            day_high=186.20,
            day_low=184.30,
            volume=45000000,
            currency="USD",
            exchange="NMS",
            market_time=datetime(2024, 3, 1, 16, 0, 0),
        )
        resp = client.get("/api/v1/stocks/AAPL/quote")
        assert resp.status_code == 200
        data = resp.json()
        assert data["symbol"] == "AAPL"
        assert data["price"] == 185.92
        assert data["previous_close"] == 184.25
        assert data["currency"] == "USD"


class TestOpenAPIDoc:
    """测试 14: OpenAPI 文档端点"""

    def test_openapi_json_accessible(self):
        resp = client.get("/openapi.json")
        assert resp.status_code == 200
        data = resp.json()
        assert data["info"]["title"] == "VT YFinance Proxy"
        assert data["info"]["version"] == "0.1.0"
        paths = list(data["paths"].keys())
        assert "/health" in paths
        assert "/finance-data/yfinance/profile" in paths
        assert "/finance-data/yfinance/all" in paths
        assert "/api/v1/stocks/{symbol}/daily" in paths

    def test_swagger_ui_accessible(self):
        resp = client.get("/docs")
        assert resp.status_code == 200

    def test_redoc_accessible(self):
        resp = client.get("/redoc")
        assert resp.status_code == 200


class TestProxyConfiguration:
    """测试 15: 代理开关配置"""

    @patch.dict("os.environ", {"USE_PROXY": "true", "YFINANCE_PROXY": "http://proxy:8080"})
    def test_proxy_enabled_returns_url(self):
        from app.services.finance_data_service import _get_proxy
        assert _get_proxy() == "http://proxy:8080"

    @patch.dict("os.environ", {"USE_PROXY": "false", "YFINANCE_PROXY": "http://proxy:8080"})
    def test_proxy_disabled_returns_none(self):
        from app.services.finance_data_service import _get_proxy
        assert _get_proxy() is None

    @patch.dict("os.environ", {"YFINANCE_PROXY": "http://proxy:8080"}, clear=True)
    def test_use_proxy_not_set_defaults_to_disabled(self):
        from app.services.finance_data_service import _get_proxy
        assert _get_proxy() is None

    @patch.dict("os.environ", {"USE_PROXY": "true"}, clear=True)
    def test_proxy_enabled_but_no_url_returns_none(self):
        from app.services.finance_data_service import _get_proxy
        assert _get_proxy() is None

    @patch.dict("os.environ", {"USE_PROXY": "1", "YFINANCE_PROXY": "socks5://proxy:1080"})
    def test_use_proxy_accepts_1(self):
        from app.services.finance_data_service import _get_proxy
        assert _get_proxy() == "socks5://proxy:1080"

    @patch.dict("os.environ", {"USE_PROXY": "yes", "YFINANCE_PROXY": "https://proxy:8443"})
    def test_use_proxy_accepts_yes(self):
        from app.services.finance_data_service import _get_proxy
        assert _get_proxy() == "https://proxy:8443"

    @patch.dict("os.environ", {"USE_PROXY": "true", "YFINANCE_PROXY": "http://proxy:8080"})
    def test_legacy_service_proxy_enabled(self):
        from app.services.yfinance_service import _get_proxy
        assert _get_proxy() == "http://proxy:8080"

    @patch.dict("os.environ", {"USE_PROXY": "false", "YFINANCE_PROXY": "http://proxy:8080"})
    def test_legacy_service_proxy_disabled(self):
        from app.services.yfinance_service import _get_proxy
        assert _get_proxy() is None
