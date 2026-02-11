# VT YFinance Proxy

面向内网的 Yahoo Finance 数据代理服务，提供 RESTful API 供其他服务器获取金融交易数据。

## 功能
- 股票日 K 线（OHLCV）
- VIX 日 K 线（^VIX）
- 股票最新行情

## 运行环境
- Python 3.10+

## 虚拟环境
```bash
python -m venv .venv
source .venv/bin/activate
```

## 安装依赖
```bash
pip install -e .
```

## 启动服务
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## systemd 一键安装
在项目根目录执行：
```bash
bash scripts/install_systemd.sh
```

可选环境变量：
- `HOST`（默认 0.0.0.0）
- `PORT`（默认 8000）
- `USER_NAME`、`GROUP_NAME`（默认当前用户）
- `PYTHON_BIN`（默认 python3）
- `VENV_DIR`（默认 .venv）
- `LOG_DIR`（默认 /var/log/vt-yfinance-proxy）
- `LOG_FILE`（默认 /var/log/vt-yfinance-proxy/app.log）

日志保留策略：
- systemd 输出写入 `LOG_FILE`
- logrotate 每天轮转，仅保留 1 天

## API 示例
- `GET /health`
- `GET /api/v1/stocks/{symbol}/daily?start=YYYY-MM-DD&end=YYYY-MM-DD`
- `GET /api/v1/vix/daily?start=YYYY-MM-DD&end=YYYY-MM-DD`
- `GET /api/v1/stocks/{symbol}/quote`

## 扩展建议
- 新增更多指数或期货数据端点
- 增加缓存与限流
- 增加鉴权与访问控制
# vt-yfinance-proxy
