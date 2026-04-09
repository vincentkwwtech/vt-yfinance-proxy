# Finance Data Proxy - yfinance API

基于 yfinance 开源项目封装的金融数据 API 服务。

## 功能特性

提供以下 8 个接口，基础路径：`/finance-data/yfinance`

### 1. 公司简况 (`/profile`)
获取公司基本信息，包括：
- 公司名称、行业、市值
- 业务简介、网站、员工数
- 地址、电话、交易所等

**示例请求：**
```bash
curl "http://localhost:8000/finance-data/yfinance/profile?ticker=AAPL"
```

### 2. 股东信息 (`/shareholders`)
获取股东持股情况：
- 主要股东列表
- 机构持股人
- 内部持股比例
- 共同基金持股

**示例请求：**
```bash
curl "http://localhost:8000/finance-data/yfinance/shareholders?ticker=AAPL"
```

### 3. 公司行动 (`/actions`)
获取公司历史行动：
- 派息历史
- 拆股记录
- 综合行动记录

**示例请求：**
```bash
curl "http://localhost:8000/finance-data/yfinance/actions?ticker=AAPL"
```

### 4. 分析师预测 (`/analyst`)
获取分析师评级与预测：
- 升级/降级历史
- 综合评级统计
- 目标价预测（平均、最高、最低）
- 分析师数量

**示例请求：**
```bash
curl "http://localhost:8000/finance-data/yfinance/analyst?ticker=AAPL"
```

### 5. 财务情况 (`/financial`)
获取完整财务报表：
- 利润表（年度 + 季度）
- 资产负债表（年度 + 季度）
- 现金流量表（年度 + 季度）
- 关键财务指标（PE、ROE、负债率、增长率等）

**示例请求：**
```bash
curl "http://localhost:8000/finance-data/yfinance/financial?ticker=AAPL"
```

### 6. 期权链 (`/optionchain`)
获取期权数据：
- 所有到期日列表
- 指定到期日的看涨/看跌期权详情

**示例请求：**
```bash
# 获取所有到期日
curl "http://localhost:8000/finance-data/yfinance/optionchain?ticker=AAPL"

# 获取指定到期日的期权链
curl "http://localhost:8000/finance-data/yfinance/optionchain?ticker=AAPL&expiration=2024-12-20"
```

### 7. K线数据 (`/kline`)
获取历史行情数据（OHLCV）：
- 支持多种时间周期（1天~最大）
- 支持多种K线间隔（1分钟~3个月）
- 可包含盘前盘后数据

**参数说明：**
- `period`: 时间周期 - 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max
- `interval`: K线间隔 - 1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo
- `prepost`: 是否包含盘前盘后（默认 false）

**示例请求：**
```bash
# 近2年日K线
curl "http://localhost:8000/finance-data/yfinance/kline?ticker=AAPL&period=2y&interval=1d"

# 近5日分时（1分钟）
curl "http://localhost:8000/finance-data/yfinance/kline?ticker=AAPL&period=5d&interval=1m"

# 过去1天分时（包含盘前盘后）
curl "http://localhost:8000/finance-data/yfinance/kline?ticker=AAPL&period=1d&interval=1m&prepost=true"
```

### 8. 所有数据 (`/all`)
一次性获取以上所有数据的汇总（不包括详细期权链和自定义K线参数）

**示例请求：**
```bash
curl "http://localhost:8000/finance-data/yfinance/all?ticker=AAPL"
```

**返回格式：**
```json
{
  "ticker": "AAPL",
  "profile": { ... },
  "shareholders": { ... },
  "actions": { ... },
  "analyst": { ... },
  "financial": { ... },
  "optionchain": { ... },
  "kline": { ... }
}
```

## 配置

### 代理设置

如果你所在的地区需要代理访问 Yahoo Finance，可以通过环境变量配置：

```bash
# 方法1：直接设置环境变量
export YFINANCE_PROXY=http://localhost:2080

# 方法2：创建 .env 文件
cp .env.example .env
# 编辑 .env 文件，设置 YFINANCE_PROXY
```

支持的代理格式：
- HTTP 代理：`http://localhost:2080`
- HTTPS 代理：`https://proxy.example.com:8080`
- SOCKS5 代理：`socks5://localhost:1080`

### 端口和主机配置

默认配置：
- 主机：0.0.0.0（监听所有网络接口）
- 端口：8000

可通过环境变量修改：
```bash
export PORT=8080
export HOST=127.0.0.1
```

## 快速开始

### 开发环境
```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 启动服务
python main.py
```

### 生产环境部署

**方式一：Systemd 部署**
```bash
./deploy-systemd.sh
```

**方式二：Docker Compose 部署（推荐）**
```bash
# 可选：创建 .env 文件配置代理等
cp .env.example .env

# 启动服务
docker compose up -d

# 查看日志
docker compose logs -f

# 停止服务
docker compose down
```

**方式三：Docker 单容器部署**
```bash
./deploy-docker.sh
```

详见：[部署文档](DEPLOYMENT.md) | [快速参考](DEPLOY_QUICK.md)

### 访问 API 文档
启动后访问：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 原有接口

原有接口保留在 `/api/v1` 路径下：

- `GET /api/v1/stocks/{symbol}/daily` - 日K线 OHLCV 数据
- `GET /api/v1/vix/daily` - VIX 日线数据
- `GET /api/v1/stocks/{symbol}/quote` - 最新报价

## 技术栈

- **FastAPI**: 现代高性能 Web 框架
- **yfinance**: Yahoo Finance 数据获取库
- **pandas**: 数据处理
- **uvicorn**: ASGI 服务器

## 注意事项

1. **数据限制**：
   - 1分钟K线数据最多只能获取近 7-30 天
   - 内幕交易历史需要结合其他数据源（如 SEC EDGAR）
   - 分析师研报只有汇总数据，无原始报告

2. **数据来源**：
   - 所有数据来自 Yahoo Finance
   - 数据更新频率取决于 Yahoo Finance 的更新

3. **错误处理**：
   - 无效股票代码返回 404
   - 服务器错误返回 500 及详细错误信息

4. **访问限制**：
   - Yahoo Finance 有请求频率限制，短时间内大量请求可能会被限流（429错误）
   - 建议在生产环境中添加请求缓存和重试机制
   - 某些地区可能需要配置代理才能访问 Yahoo Finance

5. **代理配置**：
   - 如果遇到连接问题，请检查 YFINANCE_PROXY 环境变量是否正确设置
   - 确保代理服务器正常运行且可访问

## 示例股票代码

- AAPL - 苹果
- MSFT - 微软
- GOOGL - 谷歌
- TSLA - 特斯拉
- AMZN - 亚马逊
- META - Meta（Facebook）

## 许可

本项目基于 yfinance 开源项目构建。
