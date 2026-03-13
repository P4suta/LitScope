"""Tests for works endpoints."""

from fastapi.testclient import TestClient

from litscope.api.app import create_app
from litscope.storage.database import Database


class TestListWorks:
    def test_list_works(self, api_client: TestClient) -> None:
        resp = api_client.get("/api/v1/works")
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 1
        assert body["page"] == 1
        assert body["page_size"] == 20
        assert len(body["items"]) == 1
        assert body["items"][0]["work_id"] == "test-work"
        assert body["items"][0]["title"] == "Test Title"

    def test_list_works_pagination(self, api_client: TestClient) -> None:
        resp = api_client.get("/api/v1/works?page=2&page_size=10")
        assert resp.status_code == 200
        body = resp.json()
        assert body["page"] == 2
        assert body["page_size"] == 10
        assert body["items"] == []

    def test_list_works_filter_by_author(self, api_client: TestClient) -> None:
        resp = api_client.get("/api/v1/works?author=Test+Author")
        assert resp.status_code == 200
        assert resp.json()["total"] == 1

    def test_list_works_filter_by_author_no_match(self, api_client: TestClient) -> None:
        resp = api_client.get("/api/v1/works?author=Nobody")
        assert resp.status_code == 200
        assert resp.json()["total"] == 0

    def test_list_works_filter_by_genre(self, api_client: TestClient) -> None:
        resp = api_client.get("/api/v1/works?genre=Fiction")
        assert resp.status_code == 200
        assert resp.json()["total"] == 0  # no genre set in fixture

    def test_list_works_search(self, api_client: TestClient) -> None:
        resp = api_client.get("/api/v1/works?search=Test")
        assert resp.status_code == 200
        assert resp.json()["total"] == 1

    def test_list_works_search_no_match(self, api_client: TestClient) -> None:
        resp = api_client.get("/api/v1/works?search=zzzznothing")
        assert resp.status_code == 200
        assert resp.json()["total"] == 0

    def test_list_works_empty_db(self, tmp_db: Database) -> None:
        app = create_app(db=tmp_db)
        with TestClient(app) as client:
            resp = client.get("/api/v1/works")
            assert resp.status_code == 200
            assert resp.json()["total"] == 0


class TestGetWork:
    def test_get_work_detail(self, api_client: TestClient) -> None:
        resp = api_client.get("/api/v1/works/test-work")
        assert resp.status_code == 200
        body = resp.json()
        assert body["work_id"] == "test-work"
        assert body["title"] == "Test Title"
        assert len(body["chapters"]) == 2
        assert body["chapters"][0]["chapter_id"] == "test-work::ch000"
        assert body["chapters"][0]["position"] == 0
        assert isinstance(body["analyses_run"], list)
        assert "vocabulary_frequency" in body["analyses_run"]

    def test_get_work_not_found(self, api_client: TestClient) -> None:
        resp = api_client.get("/api/v1/works/nonexistent")
        assert resp.status_code == 404
