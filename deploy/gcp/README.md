# GCP Cloud Run Deployment

This project can be deployed to Google Cloud using:

- Artifact Registry for storing Docker images
- Cloud Run for serving the API
- Revision tags for blue-green style traffic switching

## 1. Login to Google Cloud

```bash
gcloud auth login
```

## 2. Deploy a tagged revision

```bash
PROJECT_ID=<your-project-id> \
REGION=asia-southeast1 \
SERVICE_NAME=fraud-api \
TRAFFIC_TAG=green \
bash scripts/gcp-cloudrun-deploy.sh
```

This will:

- enable required APIs
- create Artifact Registry if needed
- build and push the Docker image
- deploy a Cloud Run revision with `--no-traffic`

## 3. Shift traffic to the new revision

```bash
SERVICE_NAME=fraud-api REGION=asia-southeast1 TRAFFIC_TAG=green bash scripts/gcp-cloudrun-switch.sh
```

## 4. Roll back to the previous revision

If you deployed the previous stable version with tag `blue`, switch back with:

```bash
SERVICE_NAME=fraud-api REGION=asia-southeast1 TRAFFIC_TAG=blue bash scripts/gcp-cloudrun-switch.sh
```
