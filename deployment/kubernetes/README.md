# Kubernetes Deployment

This folder mirrors the deployment pattern from the course lecture:

- wrap the model with `FastAPI`
- package it as a Docker image
- deploy it with a Kubernetes `Deployment`
- expose it with a `NodePort` `Service`

## Prerequisites

- Docker Desktop or Docker Engine
- `kind`
- `kubectl`

## 1. Create a local three-node cluster

```bash
kind create cluster --name mlops-cluster --config deployment/kubernetes/kind-three-node-cluster.yaml
kubectl get nodes
```

## 2. Build the API image and load it into kind

```bash
docker build -t ghcr.io/team-5-fraud-dectection/mlops-fraud-detection:latest .
kind load docker-image ghcr.io/team-5-fraud-dectection/mlops-fraud-detection:latest --name mlops-cluster
```

## 3. Deploy the API

```bash
kubectl apply -k deployment/kubernetes
kubectl get pods,svc
kubectl rollout status deployment/ml-api
```

## 4. Test the live service

Swagger docs:

```text
http://localhost:30007/docs
```

Health endpoint:

```bash
curl http://127.0.0.1:30007/health
```

Metrics endpoint:

```bash
curl http://127.0.0.1:30007/metrics
```
