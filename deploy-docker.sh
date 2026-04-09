#!/usr/bin/env bash
set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IMAGE_NAME="vt-yfinance-proxy"
CONTAINER_NAME="vt-yfinance-proxy"
HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8000}"
YFINANCE_PROXY="${YFINANCE_PROXY:-}"

echo "Building Docker image: ${IMAGE_NAME}"
docker build -t "${IMAGE_NAME}" "${APP_DIR}"

# Stop existing container if running
if docker ps -q -f "name=${CONTAINER_NAME}" | grep -q .; then
  echo "Stopping existing container: ${CONTAINER_NAME}"
  docker stop "${CONTAINER_NAME}"
  docker rm "${CONTAINER_NAME}"
elif docker ps -aq -f "name=${CONTAINER_NAME}" | grep -q .; then
  echo "Removing stopped container: ${CONTAINER_NAME}"
  docker rm "${CONTAINER_NAME}"
fi

DOCKER_ARGS=(
  -d
  --name "${CONTAINER_NAME}"
  -p "${PORT}:8000"
  --restart unless-stopped
  -e "HOST=${HOST}"
  -e "PORT=8000"
)

if [[ -n "${YFINANCE_PROXY}" ]]; then
  DOCKER_ARGS+=(-e "YFINANCE_PROXY=${YFINANCE_PROXY}")
fi

echo "Starting container: ${CONTAINER_NAME}"
docker run "${DOCKER_ARGS[@]}" "${IMAGE_NAME}"

echo "Container started: ${CONTAINER_NAME}"
echo "API docs: http://localhost:${PORT}/docs"
docker logs "${CONTAINER_NAME}"
