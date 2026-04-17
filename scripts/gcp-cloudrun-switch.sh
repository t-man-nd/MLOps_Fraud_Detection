#!/usr/bin/env bash

set -euo pipefail

SERVICE_NAME="${SERVICE_NAME:-${1:-fraud-api}}"
REGION="${REGION:-${2:-asia-southeast1}}"
TRAFFIC_TAG="${TRAFFIC_TAG:-${3:-}}"

if [[ -z "$TRAFFIC_TAG" ]]; then
  echo "Usage: SERVICE_NAME=fraud-api REGION=asia-southeast1 TRAFFIC_TAG=<blue|green> bash scripts/gcp-cloudrun-switch.sh"
  exit 1
fi

gcloud run services update-traffic "$SERVICE_NAME" \
  --region "$REGION" \
  --to-tags "${TRAFFIC_TAG}=100"

echo "Switched live traffic for ${SERVICE_NAME} to tag ${TRAFFIC_TAG}."
