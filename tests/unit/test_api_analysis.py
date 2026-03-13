"""Tests for analysis endpoints."""

import pytest
from fastapi.testclient import TestClient

from litscope.api.app import create_app
from litscope.storage.database import Database


class TestVocabularyEndpoint:
    def test_vocabulary_success(self, api_client: TestClient) -> None:
        resp = api_client.get("/api/v1/works/test-work/vocabulary")
        assert resp.status_code == 200
        body = resp.json()
        assert body["work_id"] == "test-work"
        assert body["total_tokens"] == 20
        assert body["unique_lemmas"] == 12
        assert body["ttr"] == pytest.approx(0.6)
        assert body["hapax_ratio"] == pytest.approx(0.4)
        assert body["yules_k"] == pytest.approx(120.0)
        assert body["mtld"] == pytest.approx(45.0)
        assert body["zipf_alpha"] == pytest.approx(1.5)
        assert body["zipf_r_squared"] == pytest.approx(0.95)
        assert body["zipf_intercept"] == pytest.approx(2.0)
        assert len(body["top_words"]) == 3
        assert body["top_words"][0]["lemma"] == "the"

    def test_vocabulary_top_n(self, api_client: TestClient) -> None:
        resp = api_client.get("/api/v1/works/test-work/vocabulary?top_n=1")
        assert resp.status_code == 200
        assert len(resp.json()["top_words"]) == 1

    def test_vocabulary_not_run(self, seeded_db: Database) -> None:
        app = create_app(db=seeded_db)
        with TestClient(app) as client:
            resp = client.get("/api/v1/works/test-work/vocabulary")
            assert resp.status_code == 404
            assert "not run" in resp.json()["detail"]

    def test_vocabulary_work_not_found(self, api_client: TestClient) -> None:
        resp = api_client.get("/api/v1/works/nonexistent/vocabulary")
        assert resp.status_code == 404


class TestSyntaxEndpoint:
    def test_syntax_success(self, api_client: TestClient) -> None:
        resp = api_client.get("/api/v1/works/test-work/syntax")
        assert resp.status_code == 200
        body = resp.json()
        assert body["work_id"] == "test-work"
        assert len(body["pos_distribution"]) == 6
        assert body["pos_distribution"][0]["pos"] == "NOUN"
        assert len(body["pos_transitions"]) == 2
        assert len(body["sentence_openings"]) == 2
        assert body["active_voice_count"] == 3
        assert body["passive_voice_count"] == 0
        assert body["passive_ratio"] == pytest.approx(0.0)

    def test_syntax_not_run(self, seeded_db: Database) -> None:
        app = create_app(db=seeded_db)
        with TestClient(app) as client:
            resp = client.get("/api/v1/works/test-work/syntax")
            assert resp.status_code == 404

    def test_syntax_work_not_found(self, api_client: TestClient) -> None:
        resp = api_client.get("/api/v1/works/nonexistent/syntax")
        assert resp.status_code == 404


class TestReadabilityEndpoint:
    def test_readability_success(self, api_client: TestClient) -> None:
        resp = api_client.get("/api/v1/works/test-work/readability")
        assert resp.status_code == 200
        body = resp.json()
        assert body["work_id"] == "test-work"
        assert body["flesch_kincaid_grade"] == pytest.approx(5.2)
        assert body["coleman_liau_index"] == pytest.approx(7.1)
        assert body["ari"] == pytest.approx(4.8)
        assert body["mean_sentence_length"] == pytest.approx(5.67)
        assert body["median_sentence_length"] == pytest.approx(6.0)
        assert body["min_sentence_length"] == 5
        assert body["max_sentence_length"] == 6

    def test_readability_not_run(self, seeded_db: Database) -> None:
        app = create_app(db=seeded_db)
        with TestClient(app) as client:
            resp = client.get("/api/v1/works/test-work/readability")
            assert resp.status_code == 404

    def test_readability_work_not_found(self, api_client: TestClient) -> None:
        resp = api_client.get("/api/v1/works/nonexistent/readability")
        assert resp.status_code == 404


class TestReadabilityWithoutSentenceLength:
    def test_readability_without_sentence_length(self, seeded_db: Database) -> None:
        """Readability without sentence_length returns None for those."""
        conn = seeded_db.conn
        conn.execute(
            "INSERT INTO analysis_results (id, analyzer_name, work_id, metrics, data) "
            "VALUES (nextval('seq_analysis_results'), ?, ?, ?, ?)",
            [
                "readability",
                "test-work",
                '{"flesch_kincaid_grade": 5.2, "coleman_liau_index": 7.1, "ari": 4.8}',
                "{}",
            ],
        )
        app = create_app(db=seeded_db)
        with TestClient(app) as client:
            resp = client.get("/api/v1/works/test-work/readability")
            assert resp.status_code == 200
            body = resp.json()
            assert body["mean_sentence_length"] is None
            assert body["min_sentence_length"] is None


class TestFutureAnalysisStubs:
    @pytest.mark.parametrize(
        "endpoint",
        ["sentiment", "characters", "dialogue", "ngrams", "stylometry"],
    )
    def test_future_stubs_return_404(
        self, api_client: TestClient, endpoint: str
    ) -> None:
        resp = api_client.get(f"/api/v1/works/test-work/{endpoint}")
        assert resp.status_code == 404
        assert "not yet implemented" in resp.json()["detail"]

    @pytest.mark.parametrize(
        "endpoint",
        ["sentiment", "characters", "dialogue", "ngrams", "stylometry"],
    )
    def test_future_stubs_work_not_found(
        self, api_client: TestClient, endpoint: str
    ) -> None:
        resp = api_client.get(f"/api/v1/works/nonexistent/{endpoint}")
        assert resp.status_code == 404
