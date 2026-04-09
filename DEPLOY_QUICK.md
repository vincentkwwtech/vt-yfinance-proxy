# 快速部署参考

## 开发环境

```bash
pip install -r requirements.txt
python main.py
```

## Systemd 部署

```bash
./deploy-systemd.sh
```

## Docker Compose 部署（推荐）

```bash
cp .env.example .env   # 按需编辑
docker compose up -d
```

## Docker 单容器部署

```bash
./deploy-docker.sh
```

## 配置代理

```bash
export YFINANCE_PROXY=http://localhost:2080
```

## API 文档

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
