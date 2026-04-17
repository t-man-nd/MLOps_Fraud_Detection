#!/usr/bin/env bash

set -euo pipefail

PROJECT_ID="${PROJECT_ID:-${1:-}}"
REGION="${REGION:-${2:-asia-southeast1}}"
SERVICE_NAME="${SERVICE_NAME:-${3:-fraud-api}}"
ARTIFACT_REPO="${ARTIFACT_REPO:-${4:-fraud-api}}"
IMAGE_NAME="${IMAGE_NAME:-ieee-fraud-api}"
IMAGE_TAG="${IMAGE_TAG:-$(date +%Y%m%d-%H%M%S)}"
TRAFFIC_TAG="${TRAFFIC_TAG:-green}"
LOCAL_IMAGE="${LOCAL_IMAGE:-ieee-fraud-api:latest}"
PORT="${PORT:-8000}"

if [[ -z "$PROJECT_ID" ]]; then
  echo "Usage: PROJECT_ID=<gcp-project-id> [REGION=asia-southeast1] [SERVICE_NAME=fraud-api] bash scripts/gcp-cloudrun-deploy.sh"
  exit 1
fi

if ! command -v gcloud >/dev/null 2>&1; then
  echo "gcloud is not installed."
  exit 1
fi

ACTIVE_ACCOUNT="$(gcloud auth list --filter=status:ACTIVE --format='value(account)' 2>/dev/null || true)"
if [[ -z "$ACTIVE_ACCOUNT" ]]; then
  echo "No active gcloud account found. Run: gcloud auth login"
  exit 1
fi

gcloud config set project "$PROJECT_ID" >/dev/null

echo "Using project: $PROJECT_ID"
echo "Using region: $REGION"
echo "Active account: $ACTIVE_ACCOUNT"

gcloud services enable \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com

if ! gcloud artifacts repositories describe "$ARTIFACT_REPO" --location "$REGION" >/dev/null 2>&1; then
  gcloud artifacts repositories create "$ARTIFACT_REPO" \
    --repository-format=docker \
    --location="$REGION" \
    --description="Fraud API container registry"
fi

gcloud auth configure-docker "${REGION}-docker.pkg.dev" --quiet

REMOTE_IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/${ARTIFACT_REPO}/${IMAGE_NAME}:${IMAGE_TAG}"

echo "Building local image ${LOCAL_IMAGE}"
docker build -t "$LOCAL_IMAGE" .
docker tag "$LOCAL_IMAGE" "$REMOTE_IMAGE"
docker push "$REMOTE_IMAGE"

echo "Deploying tagged revision '${TRAFFIC_TAG}' to Cloud Run without shifting traffic yet"
gcloud run deploy "$SERVICE_NAME" \
  --image "$REMOTE_IMAGE" \
  --region "$REGION" \
  --allow-unauthenticated \
  --port "$PORT" \
  --tag "$TRAFFIC_TAG" \
  --no-traffic

echo
echo "Deployed revision tag '${TRAFFIC_TAG}'."
echo "When you are ready to route live traffic, run:"
echo "gcloud run services update-traffic ${SERVICE_NAME} --region ${REGION} --to-tags ${TRAFFIC_TAG}=100"
echo
echo "Service URL:"
gcloud run services describe "$SERVICE_NAME" --region "$REGION" --format='value(status.url)'
