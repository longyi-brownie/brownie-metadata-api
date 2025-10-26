"""Test health check endpoint."""

from fastapi.testclient import TestClient


def test_health_check(client: TestClient):
    """Test health check endpoint returns 200."""
    response = client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] in ["healthy", "unhealthy"]
    assert "timestamp" in data
    assert data["version"] == "0.1.0"
    assert "database" in data


def test_metrics_endpoint(client: TestClient):
    """Test metrics endpoint returns Prometheus format."""
    response = client.get("/metrics")
    assert response.status_code == 200
    # Check content-type starts with text/plain (version may vary)
    assert response.headers["content-type"].startswith("text/plain")
    assert "charset=utf-8" in response.headers["content-type"]
    assert "http_requests_total" in response.text
