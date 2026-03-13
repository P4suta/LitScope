"""Tests for compare endpoint."""

from fastapi.testclient import TestClient

from litscope.api.app import create_app
from litscope.storage.database import Database


class TestCompareEndpoint:
    def test_compare_single_work(self, api_client: TestClient) -> None:
        resp = api_client.get("/api/v1/compare?work_id=test-work")
        assert resp.status_code == 200
        body = resp.json()
        assert len(body) == 1
        assert body[0]["work_id"] == "test-work"
        assert body[0]["title"] == "Test Title"
        assert "vocabulary_frequency.total_tokens" in body[0]["metrics"]

    def test_compare_work_not_found(self, api_client: TestClient) -> None:
        resp = api_client.get("/api/v1/compare?work_id=nonexistent")
        assert resp.status_code == 404

    def test_compare_too_many_works(self, api_client: TestClient) -> None:
        ids = "&".join(f"work_id=w{i}" for i in range(6))
        resp = api_client.get(f"/api/v1/compare?{ids}")
        assert resp.status_code == 400
        assert "Maximum 5" in resp.json()["detail"]

    def test_compare_no_analysis(self, seeded_db: Database) -> None:
        """Work exists but has no analysis — returns empty metrics."""
        app = create_app(db=seeded_db)
        with TestClient(app) as client:
            resp = client.get("/api/v1/compare?work_id=test-work")
            assert resp.status_code == 200
            assert resp.json()[0]["metrics"] == {}

    def test_compare_multiple_works(
        self, seeded_db_with_analysis: Database
    ) -> None:
        """Add a second work and compare two."""
        conn = seeded_db_with_analysis.conn
        conn.execute(
            "INSERT INTO works (work_id, title, author, file_path, file_hash, "
            "word_count, sent_count, chap_count) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            ["work-2", "Second Work", "Other Author", "/p", "hash2", 10, 2, 1],
        )
        app = create_app(db=seeded_db_with_analysis)
        with TestClient(app) as client:
            resp = client.get(
                "/api/v1/compare?work_id=test-work&work_id=work-2"
            )
            assert resp.status_code == 200
            assert len(resp.json()) == 2
