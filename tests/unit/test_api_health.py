"""Tests for health and status endpoints."""

from fastapi.testclient import TestClient


class TestHealthEndpoint:
    def test_health_returns_ok(self, api_client: TestClient) -> None:
        resp = api_client.get("/api/v1/health")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "ok"
        assert body["version"] == "0.1.0"


class TestStatusEndpoint:
    def test_status_returns_counts(self, api_client: TestClient) -> None:
        resp = api_client.get("/api/v1/status")
        assert resp.status_code == 200
        body = resp.json()
        assert body["works"] == 1
        assert body["chapters"] == 2
        assert body["sentences"] == 3
        assert body["tokens"] == 20
        assert isinstance(body["analyzers_available"], list)
        assert len(body["analyzers_available"]) > 0
