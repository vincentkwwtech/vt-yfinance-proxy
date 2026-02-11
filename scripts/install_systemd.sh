#!/usr/bin/env bash
set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SERVICE_NAME="vt-yfinance-proxy"
PYTHON_BIN="${PYTHON_BIN:-python3}"
HOST="${HOST:-10.175.127.13}"
PORT="${PORT:-8000}"
USER_NAME="${USER_NAME:-$USER}"
GROUP_NAME="${GROUP_NAME:-$USER}"
VENV_DIR="${VENV_DIR:-${APP_DIR}/.venv}"
LOG_DIR="${LOG_DIR:-/var/log/vt-yfinance-proxy}"
LOG_FILE="${LOG_FILE:-${LOG_DIR}/app.log}"

if [[ -x "${PYTHON_BIN}" ]]; then
  RESOLVED_PYTHON_BIN="${PYTHON_BIN}"
else
  RESOLVED_PYTHON_BIN="$(command -v "${PYTHON_BIN}" || true)"
fi

if [[ -z "${RESOLVED_PYTHON_BIN}" ]]; then
  if [[ -x "/usr/bin/python3" ]]; then
    RESOLVED_PYTHON_BIN="/usr/bin/python3"
  elif [[ -x "/usr/bin/python" ]]; then
    RESOLVED_PYTHON_BIN="/usr/bin/python"
  fi
fi

if [[ -z "${RESOLVED_PYTHON_BIN}" ]]; then
  echo "Python not found: ${PYTHON_BIN}" >&2
  exit 1
fi

if [[ ! -d "${VENV_DIR}" ]]; then
  "${RESOLVED_PYTHON_BIN}" -m venv "${VENV_DIR}"
fi

"${VENV_DIR}/bin/python" -m pip install -U pip
"${VENV_DIR}/bin/python" -m pip install -e "${APP_DIR}"

SERVICE_PATH="/etc/systemd/system/${SERVICE_NAME}.service"
LOGROTATE_PATH="/etc/logrotate.d/${SERVICE_NAME}"

sudo mkdir -p "${LOG_DIR}"
sudo chown "${USER_NAME}:${GROUP_NAME}" "${LOG_DIR}"

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
StandardOutput=append:${LOG_FILE}
StandardError=append:${LOG_FILE}
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

echo "Configuring logrotate at ${LOGROTATE_PATH}"
sudo tee "${LOGROTATE_PATH}" > /dev/null <<EOF
${LOG_FILE} {
  daily
  rotate 1
  maxage 1
  missingok
  notifempty
  copytruncate
}
EOF

sudo systemctl daemon-reload
sudo systemctl enable "${SERVICE_NAME}.service"
sudo systemctl restart "${SERVICE_NAME}.service"

sudo systemctl status "${SERVICE_NAME}.service" --no-pager

echo "Service installed and started: ${SERVICE_NAME}"
