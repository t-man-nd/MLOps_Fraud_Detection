from fastapi.testclient import TestClient

from src import api


client = TestClient(api.app)


def test_health_reports_raw_pipeline_status():
    response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert "raw_pipeline_ready" in payload
    assert payload["raw_pipeline_ready"] is False


def test_predict_raw_returns_503_when_pipeline_artifact_is_missing():
    response = client.post(
        "/predict_raw",
        json={"records": [{"TransactionAmt": 100.0}]},
    )

    assert response.status_code == 503
    assert "Raw prediction pipeline is unavailable" in response.json()["detail"]
