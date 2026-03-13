"""Tests for timeline endpoint."""

from fastapi.testclient import TestClient

from litscope.api.app import create_app
from litscope.storage.database import Database


class TestTimelineEndpoint:
    def test_vocabulary_timeline(self, api_client: TestClient) -> None:
        resp = api_client.get("/api/v1/timeline/vocabulary")
        assert resp.status_code == 200
        body = resp.json()
        points = body["points"]
        assert len(points) == 1
        assert points[0]["work_id"] == "test-work"
        assert points[0]["title"] == "Test Title"
        assert points[0]["pub_year"] == 1920
        assert points[0]["ttr"] == 0.6
        assert points[0]["mtld"] == 45.0
        assert points[0]["hapax_ratio"] == 0.4
        assert points[0]["unique_lemmas"] == 12

    def test_vocabulary_timeline_empty_db(self, tmp_db: Database) -> None:
        """No works → empty points."""
        app = create_app(db=tmp_db)
        with TestClient(app) as client:
            resp = client.get("/api/v1/timeline/vocabulary")
            assert resp.status_code == 200
            assert resp.json()["points"] == []

    def test_vocabulary_timeline_no_analysis(self, seeded_db: Database) -> None:
        """Work exists but no analysis results → null metrics."""
        app = create_app(db=seeded_db)
        with TestClient(app) as client:
            resp = client.get("/api/v1/timeline/vocabulary")
            assert resp.status_code == 200
            points = resp.json()["points"]
            assert len(points) == 1
            assert points[0]["ttr"] is None
            assert points[0]["unique_lemmas"] is None

    def test_vocabulary_timeline_excludes_null_pub_year(
        self, seeded_db_with_analysis: Database
    ) -> None:
        """Works without pub_year are excluded."""
        conn = seeded_db_with_analysis.conn
        conn.execute(
            "INSERT INTO works (work_id, title, author, file_path, file_hash, "
            "pub_year, word_count, sent_count, chap_count) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            ["work-noyear", "No Year", "Author", "/p", "h", None, 10, 2, 1],
        )
        app = create_app(db=seeded_db_with_analysis)
        with TestClient(app) as client:
            resp = client.get("/api/v1/timeline/vocabulary")
            assert resp.status_code == 200
            points = resp.json()["points"]
            work_ids = [p["work_id"] for p in points]
            assert "work-noyear" not in work_ids

    def test_vocabulary_timeline_ordered_by_year(
        self, seeded_db_with_analysis: Database
    ) -> None:
        """Multiple works are returned sorted by pub_year."""
        conn = seeded_db_with_analysis.conn
        conn.execute(
            "INSERT INTO works (work_id, title, author, file_path, file_hash, "
            "pub_year, word_count, sent_count, chap_count) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            ["work-old", "Old Book", "Author", "/p", "h2", 1800, 10, 2, 1],
        )
        app = create_app(db=seeded_db_with_analysis)
        with TestClient(app) as client:
            resp = client.get("/api/v1/timeline/vocabulary")
            assert resp.status_code == 200
            points = resp.json()["points"]
            years = [p["pub_year"] for p in points]
            assert years == sorted(years)
