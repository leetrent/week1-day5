#!/usr/bin/env bash
set -euo pipefail

IMAGE_NAME="pm-mvp"
CONTAINER_NAME="pm-mvp-app"
PORT="8000"

docker build -t "${IMAGE_NAME}" .

if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
  docker rm -f "${CONTAINER_NAME}" >/dev/null
fi

docker run -d --name "${CONTAINER_NAME}" -p "${PORT}:8000" "${IMAGE_NAME}"

echo "PM MVP is running at http://localhost:${PORT}"
