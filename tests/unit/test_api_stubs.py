"""Tests for stub/future endpoints and authors endpoint."""

from fastapi.testclient import TestClient


class TestAuthorsEndpoint:
    def test_list_authors(self, api_client: TestClient) -> None:
        resp = api_client.get("/api/v1/authors")
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 1
        assert body["items"][0]["author"] == "Test Author"
        assert body["items"][0]["work_count"] == 1

    def test_list_authors_pagination(self, api_client: TestClient) -> None:
        resp = api_client.get("/api/v1/authors?page=2&page_size=10")
        assert resp.status_code == 200
        assert resp.json()["items"] == []


class TestGenresStub:
    def test_genres_not_implemented(self, api_client: TestClient) -> None:
        resp = api_client.get("/api/v1/genres/comparison")
        assert resp.status_code == 404
        assert "not yet implemented" in resp.json()["detail"]
