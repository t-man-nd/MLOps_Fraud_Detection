# Prometheus & Grafana Monitoring

This folder contains the Kubernetes monitoring assets that match the lecture flow:

- expose FastAPI metrics on `/metrics`
- install Prometheus and Grafana with Helm
- scrape the FastAPI service via `ServiceMonitor`

## 1. Install kube-prometheus-stack

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

helm upgrade --install prom \
  -n monitoring \
  --create-namespace \
  prometheus-community/kube-prometheus-stack \
  -f deployment/monitoring/kube-prometheus-stack-values.yaml
```

## 2. Apply the ServiceMonitor

```bash
kubectl apply -k deployment/monitoring
kubectl get servicemonitor -n monitoring
```

## 3. Access the dashboards

- Prometheus: `http://localhost:30300`
- Grafana: `http://localhost:30200`

## 4. Suggested validation checks

Open the Prometheus targets page:

```text
http://localhost:30300/targets
```

Useful queries:

```text
http_requests_total
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
```
