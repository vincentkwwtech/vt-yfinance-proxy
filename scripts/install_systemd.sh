#!/usr/bin/env bash
set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SERVICE_NAME="vt-yfinance-proxy"
PYTHON_BIN="${PYTHON_BIN:-python3}"
HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8000}"
USER_NAME="${USER_NAME:-$USER}"
GROUP_NAME="${GROUP_NAME:-$USER}"
VENV_DIR="${VENV_DIR:-${APP_DIR}/.venv}"

if [[ ! -x "${PYTHON_BIN}" ]]; then
  echo "Python not found: ${PYTHON_BIN}" >&2
  exit 1
fi

if [[ ! -d "${VENV_DIR}" ]]; then
  "${PYTHON_BIN}" -m venv "${VENV_DIR}"
fi

"${VENV_DIR}/bin/python" -m pip install -U pip
"${VENV_DIR}/bin/python" -m pip install -e "${APP_DIR}"

SERVICE_PATH="/etc/systemd/system/${SERVICE_NAME}.service"

echo "Creating systemd service at ${SERVICE_PATH}"

sudo tee "${SERVICE_PATH}" > /dev/null <<EOF
[Unit]
Description=VT YFinance Proxy
After=network.target

[Service]
Type=simple
User=${USER_NAME}
Group=${GROUP_NAME}
WorkingDirectory=${APP_DIR}
Environment=PYTHONUNBUFFERED=1
ExecStart=${VENV_DIR}/bin/uvicorn app.main:app --host ${HOST} --port ${PORT}
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable "${SERVICE_NAME}.service"
sudo systemctl restart "${SERVICE_NAME}.service"

sudo systemctl status "${SERVICE_NAME}.service" --no-pager

echo "Service installed and started: ${SERVICE_NAME}"
