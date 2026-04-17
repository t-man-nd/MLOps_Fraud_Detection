#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="$ROOT_DIR/deploy/bluegreen/compose.bluegreen.yml"
SWITCH_SCRIPT="$ROOT_DIR/scripts/bluegreen-switch.sh"

SLOT="${1:-}"
IMAGE_TAG="${2:-ieee-fraud-api:latest}"
WAIT_SECONDS="${WAIT_SECONDS:-120}"

if [[ "$SLOT" != "blue" && "$SLOT" != "green" ]]; then
  echo "Usage: $0 <blue|green> [image_tag]"
  exit 1
fi

SERVICE="fraud-api-${SLOT}"
IMAGE_ENV_NAME="$(echo "${SLOT}_image" | tr '[:lower:]' '[:upper:]')"

echo "Deploying ${SERVICE} with image ${IMAGE_TAG}"
env "${IMAGE_ENV_NAME}=${IMAGE_TAG}" docker compose -f "$COMPOSE_FILE" up -d "$SERVICE"

CONTAINER_ID="$(docker compose -f "$COMPOSE_FILE" ps -q "$SERVICE")"
if [[ -z "$CONTAINER_ID" ]]; then
  echo "Unable to find container for ${SERVICE}"
  exit 1
fi

SECONDS_WAITED=0
until [[ "$(docker inspect -f '{{if .State.Health}}{{.State.Health.Status}}{{else}}unknown{{end}}' "$CONTAINER_ID")" == "healthy" ]]; do
  if (( SECONDS_WAITED >= WAIT_SECONDS )); then
    echo "${SERVICE} did not become healthy within ${WAIT_SECONDS}s"
    docker logs "$CONTAINER_ID" || true
    exit 1
  fi
  sleep 5
  SECONDS_WAITED=$((SECONDS_WAITED + 5))
done

echo "${SERVICE} is healthy. Ensuring proxy is running..."
docker compose -f "$COMPOSE_FILE" up -d fraud-api-proxy
"$SWITCH_SCRIPT" "$SLOT"

echo "Blue-Green deployment completed. Active slot: ${SLOT}"
