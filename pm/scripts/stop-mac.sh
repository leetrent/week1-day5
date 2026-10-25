#!/usr/bin/env bash
set -euo pipefail

CONTAINER_NAME="pm-mvp-app"

if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
  docker stop "${CONTAINER_NAME}" >/dev/null
  docker rm "${CONTAINER_NAME}" >/dev/null
  echo "Stopped and removed ${CONTAINER_NAME}"
else
  echo "Container ${CONTAINER_NAME} was not found"
fi
