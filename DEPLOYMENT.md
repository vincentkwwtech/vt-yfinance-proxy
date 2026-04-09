# 部署文档

## 方式一：Systemd 部署（推荐）

### 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `HOST` | `0.0.0.0` | 监听地址 |
| `PORT` | `8000` | 监听端口 |
| `PYTHON_BIN` | `python3` | Python 路径 |
| `USER_NAME` | 当前用户 | 运行用户 |
| `GROUP_NAME` | 当前用户 | 运行用户组 |
| `VENV_DIR` | `.venv` | 虚拟环境目录 |
| `LOG_DIR` | `/var/log/vt-yfinance-proxy` | 日志目录 |
| `YFINANCE_PROXY` | 无 | 代理地址 |

### 安装

```bash
# 基本安装
./deploy-systemd.sh

# 自定义端口和代理
PORT=9000 YFINANCE_PROXY=http://localhost:2080 ./deploy-systemd.sh
```

### 管理

```bash
# 查看状态
sudo systemctl status vt-yfinance-proxy

# 重启
sudo systemctl restart vt-yfinance-proxy

# 查看日志
tail -f /var/log/vt-yfinance-proxy/app.log
```

## 方式二：Docker Compose 部署（推荐）

### 配置

```bash
# 复制环境变量模板
cp .env.example .env
# 编辑 .env，按需设置 YFINANCE_PROXY、PORT 等
```

`.env` 文件示例：
```env
PORT=8000
YFINANCE_PROXY=http://host.docker.internal:2080
LOG_LEVEL=INFO
```

### 启动

```bash
# 前台启动（查看日志）
docker compose up

# 后台启动
docker compose up -d

# 自定义端口
PORT=9000 docker compose up -d
```

### 管理

```bash
# 查看状态
docker compose ps

# 查看日志
docker compose logs -f

# 重启
docker compose restart

# 停止并删除容器
docker compose down

# 重新构建（代码更新后）
docker compose up -d --build
```

### 健康检查

docker-compose 已配置自动健康检查（每 30 秒检查 `/health` 端点），不健康时自动重启。

## 方式三：Docker 单容器部署

### 安装

```bash
# 基本安装
./deploy-docker.sh

# 自定义端口和代理
PORT=9000 YFINANCE_PROXY=http://host.docker.internal:2080 ./deploy-docker.sh
```

### 管理

```bash
# 查看状态
docker ps -f name=vt-yfinance-proxy

# 查看日志
docker logs -f vt-yfinance-proxy

# 重启
docker restart vt-yfinance-proxy

# 停止
docker stop vt-yfinance-proxy
```

## 代理配置

如果需要代理访问 Yahoo Finance：

```bash
# HTTP 代理
export YFINANCE_PROXY=http://localhost:2080

# HTTPS 代理
export YFINANCE_PROXY=https://proxy.example.com:8080

# SOCKS5 代理
export YFINANCE_PROXY=socks5://localhost:1080
```
