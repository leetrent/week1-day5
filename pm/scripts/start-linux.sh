#!/usr/bin/env bash
set -euo pipefail

IMAGE_NAME="pm-mvp"
CONTAINER_NAME="pm-mvp-app"
PORT="8000"
VOLUME_NAME="pm-data"
ENV_FILE=".env"

if [[ ! -f "${ENV_FILE}" ]]; then
  echo "Missing ${ENV_FILE}. Create it in the project root with OPENROUTER_API_KEY before starting." >&2
  exit 1
fi

docker build -t "${IMAGE_NAME}" .

if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
  docker rm -f "${CONTAINER_NAME}" >/dev/null
fi

docker run -d --name "${CONTAINER_NAME}" --env-file "${ENV_FILE}" -p "${PORT}:8000" -v "${VOLUME_NAME}:/app/backend/data" "${IMAGE_NAME}"

echo "PM MVP is running at http://localhost:${PORT}"
