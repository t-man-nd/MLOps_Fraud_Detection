# Blue-Green Deployment

This setup runs two API slots and one reverse proxy:

- `fraud-api-blue`
- `fraud-api-green`
- `fraud-api-proxy`

The proxy publishes the live endpoint on `http://localhost:8080` and forwards
traffic to the currently active slot.

## Start the initial blue slot

```bash
docker compose -f deploy/bluegreen/compose.bluegreen.yml up -d fraud-api-blue fraud-api-proxy
curl http://127.0.0.1:8080/health
```

## Deploy a new version to green

Build and tag a new image:

```bash
docker build -t ieee-fraud-api:green .
```

Deploy it and switch traffic only after the container is healthy:

```bash
bash scripts/bluegreen-deploy.sh green ieee-fraud-api:green
curl http://127.0.0.1:8080/health
```

## Roll back to blue

```bash
bash scripts/bluegreen-switch.sh blue
```

## Notes

- The proxy only switches when the target slot is healthy.
- `/health` is the deployment health check endpoint.
- If you later push images to cloud registry, replace the image tag argument with
  your remote image URI, for example:
  `asia-southeast1-docker.pkg.dev/<project>/fraud-api/ieee-fraud-api:v2`
