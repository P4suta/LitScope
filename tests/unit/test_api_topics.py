"""Tests for topics endpoint."""

from fastapi.testclient import TestClient

from litscope.api.app import create_app
from litscope.storage.database import Database


class TestTopicsEndpoint:
    def test_list_topics_returns_keywords(self, api_client: TestClient) -> None:
        resp = api_client.get("/api/v1/topics")
        assert resp.status_code == 200
        body = resp.json()
        assert len(body) == 1
        assert body[0]["label"] == "Test Title"
        assert body[0]["work_id"] == "test-work"
        assert body[0]["topic_id"] == 0
        keywords = body[0]["keywords"]
        assert len(keywords) > 0
        assert all("lemma" in kw and "score" in kw for kw in keywords)
        # First keyword should have score 1.0 (normalized max)
        assert keywords[0]["score"] == 1.0

    def test_list_topics_custom_top_n(self, api_client: TestClient) -> None:
        resp = api_client.get("/api/v1/topics?top_n=2")
        assert resp.status_code == 200
        body = resp.json()
        assert len(body[0]["keywords"]) <= 2

    def test_list_topics_empty_db(self, tmp_db: Database) -> None:
        """No works → empty list."""
        app = create_app(db=tmp_db)
        with TestClient(app) as client:
            resp = client.get("/api/v1/topics")
            assert resp.status_code == 200
            assert resp.json() == []

    def test_list_topics_no_word_frequencies(self, seeded_db: Database) -> None:
        """Work exists but no word_frequencies → empty keywords."""
        app = create_app(db=seeded_db)
        with TestClient(app) as client:
            resp = client.get("/api/v1/topics")
            assert resp.status_code == 200
            body = resp.json()
            assert len(body) == 1
            assert body[0]["keywords"] == []

    def test_list_topics_multiple_works(
        self, seeded_db_with_analysis: Database
    ) -> None:
        """Add a second work with word frequencies and verify both appear."""
        conn = seeded_db_with_analysis.conn
        conn.execute(
            "INSERT INTO works (work_id, title, author, file_path, file_hash, "
            "word_count, sent_count, chap_count) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            ["work-2", "Second Work", "Other Author", "/p", "hash2", 10, 2, 1],
        )
        conn.executemany(
            "INSERT INTO word_frequencies "
            "(work_id, lemma, count, tf) VALUES (?, ?, ?, ?)",
            [
                ("work-2", "the", 3, 0.30),
                ("work-2", "love", 2, 0.20),
            ],
        )
        app = create_app(db=seeded_db_with_analysis)
        with TestClient(app) as client:
            resp = client.get("/api/v1/topics")
            assert resp.status_code == 200
            body = resp.json()
            assert len(body) == 2
            # IDF for "love" (only in work-2) should be higher than "the" (in both)
            work2_topics = next(t for t in body if t["work_id"] == "work-2")
            lemmas = [kw["lemma"] for kw in work2_topics["keywords"]]
            assert "love" in lemmas
