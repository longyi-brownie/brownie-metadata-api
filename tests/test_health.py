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
    assert (
        response.headers["content-type"] == "text/plain; version=0.0.4; charset=utf-8"
    )
    assert "http_requests_total" in response.text
