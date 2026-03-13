"""Tests for ingest endpoint."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from litscope.api.app import create_app
from litscope.ingestion.pipeline import IngestionResult, IngestionSummary
from litscope.storage.database import Database


def _make_summary(
    results: list[IngestionResult] | None = None,
) -> IngestionSummary:
    return IngestionSummary(
        results=results
        or [
            IngestionResult(
                work_id="sample",
                title="Sample",
                success=True,
                chapters=2,
                sentences=3,
                tokens=20,
            )
        ]
    )


class TestIngestEndpoint:
    @patch("litscope.ingestion.pipeline.IngestionPipeline")
    def test_ingest_success(
        self, mock_pipeline_cls: MagicMock, tmp_db: Database, tmp_path: Path
    ) -> None:
        epub_dir = tmp_path / "epubs"
        epub_dir.mkdir()
        mock_pipeline_cls.return_value.ingest_directory.return_value = (
            _make_summary()
        )

        app = create_app(db=tmp_db)
        with TestClient(app) as client:
            resp = client.post(
                "/api/v1/ingest",
                json={"epub_dir": str(epub_dir)},
            )
            assert resp.status_code == 200
            body = resp.json()
            assert body["total"] == 1
            assert body["ingested"] == 1
            assert body["failed"] == 0
            assert len(body["results"]) == 1
            assert body["results"][0]["success"] is True

    def test_ingest_nonexistent_dir(self, tmp_db: Database) -> None:
        app = create_app(db=tmp_db)
        with TestClient(app) as client:
            resp = client.post(
                "/api/v1/ingest",
                json={"epub_dir": "/nonexistent/path"},
            )
            assert resp.status_code == 400
            assert "not found" in resp.json()["detail"]

    @patch("litscope.ingestion.pipeline.IngestionPipeline")
    def test_ingest_empty_dir(
        self, mock_pipeline_cls: MagicMock, tmp_db: Database, tmp_path: Path
    ) -> None:
        epub_dir = tmp_path / "empty"
        epub_dir.mkdir()
        mock_pipeline_cls.return_value.ingest_directory.return_value = (
            IngestionSummary(results=[])
        )

        app = create_app(db=tmp_db)
        with TestClient(app) as client:
            resp = client.post(
                "/api/v1/ingest",
                json={"epub_dir": str(epub_dir)},
            )
            assert resp.status_code == 200
            assert resp.json()["total"] == 0

    @patch("litscope.ingestion.pipeline.IngestionPipeline")
    def test_ingest_with_skipped(
        self, mock_pipeline_cls: MagicMock, tmp_db: Database, tmp_path: Path
    ) -> None:
        epub_dir = tmp_path / "epubs"
        epub_dir.mkdir()
        mock_pipeline_cls.return_value.ingest_directory.return_value = (
            IngestionSummary(
                results=[
                    IngestionResult(
                        work_id="sample",
                        title="Sample",
                        success=True,
                        skipped=True,
                    )
                ]
            )
        )

        app = create_app(db=tmp_db)
        with TestClient(app) as client:
            resp = client.post(
                "/api/v1/ingest",
                json={"epub_dir": str(epub_dir)},
            )
            assert resp.status_code == 200
            assert resp.json()["skipped"] == 1

    @patch("litscope.ingestion.pipeline.IngestionPipeline")
    def test_ingest_with_failure(
        self, mock_pipeline_cls: MagicMock, tmp_db: Database, tmp_path: Path
    ) -> None:
        epub_dir = tmp_path / "epubs"
        epub_dir.mkdir()
        mock_pipeline_cls.return_value.ingest_directory.return_value = (
            IngestionSummary(
                results=[
                    IngestionResult(
                        work_id="bad",
                        title="Bad",
                        success=False,
                        error="parse error",
                    )
                ]
            )
        )

        app = create_app(db=tmp_db)
        with TestClient(app) as client:
            resp = client.post(
                "/api/v1/ingest",
                json={"epub_dir": str(epub_dir)},
            )
            assert resp.status_code == 200
            body = resp.json()
            assert body["failed"] == 1
            assert body["results"][0]["error"] == "parse error"
