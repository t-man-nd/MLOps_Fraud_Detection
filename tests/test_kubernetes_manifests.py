from pathlib import Path

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def load_yaml(path: str):
    return yaml.safe_load((PROJECT_ROOT / path).read_text(encoding="utf-8"))


def test_deployment_manifest_exposes_health_probes():
    deployment = load_yaml("deployment.yaml")
    container = deployment["spec"]["template"]["spec"]["containers"][0]

    assert deployment["kind"] == "Deployment"
    assert deployment["spec"]["replicas"] == 2
    assert container["ports"][0]["name"] == "http"
    assert container["readinessProbe"]["httpGet"]["path"] == "/health"
    assert container["livenessProbe"]["httpGet"]["path"] == "/health"


def test_service_manifest_uses_nodeport_and_named_http_port():
    service = load_yaml("service.yaml")

    assert service["kind"] == "Service"
    assert service["spec"]["type"] == "NodePort"
    assert service["spec"]["selector"]["app"] == "ml-api"
    assert service["spec"]["ports"][0]["name"] == "http"
    assert service["spec"]["ports"][0]["nodePort"] == 30007


def test_servicemonitor_scrapes_metrics_endpoint():
    service_monitor = load_yaml("deployment/monitoring/servicemonitor.yaml")
    endpoint = service_monitor["spec"]["endpoints"][0]

    assert service_monitor["kind"] == "ServiceMonitor"
    assert service_monitor["spec"]["selector"]["matchLabels"]["app"] == "ml-api"
    assert endpoint["port"] == "http"
    assert endpoint["path"] == "/metrics"
