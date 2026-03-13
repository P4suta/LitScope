"""Tests for ingest endpoint."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from litscope.api.app import create_app
from litscope.api.schemas.ingest import IngestRequest
from litscope.config import LitScopeSettings
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


def _settings_with_epub_dir(epub_base: Path) -> LitScopeSettings:
    return LitScopeSettings(epub_dir=epub_base)


class TestIngestEndpoint:
    @patch("litscope.ingestion.pipeline.IngestionPipeline")
    def test_ingest_success(
        self, mock_pipeline_cls: MagicMock, tmp_db: Database, tmp_path: Path
    ) -> None:
        epub_dir = tmp_path / "epubs"
        epub_dir.mkdir()
        mock_pipeline_cls.return_value.ingest_directory.return_value = _make_summary()

        app = create_app(db=tmp_db, settings=_settings_with_epub_dir(tmp_path))
        with TestClient(app) as client:
            resp = client.post("/api/v1/ingest", json={"epub_dir": "epubs"})
            assert resp.status_code == 200
            body = resp.json()
            assert body["total"] == 1
            assert body["ingested"] == 1
            assert body["failed"] == 0
            assert len(body["results"]) == 1
            assert body["results"][0]["success"] is True

    def test_ingest_nonexistent_dir(self, tmp_db: Database, tmp_path: Path) -> None:
        app = create_app(db=tmp_db, settings=_settings_with_epub_dir(tmp_path))
        with TestClient(app) as client:
            resp = client.post("/api/v1/ingest", json={"epub_dir": "nonexistent"})
            assert resp.status_code == 400
            assert "not found" in resp.json()["detail"]

    @patch("litscope.ingestion.pipeline.IngestionPipeline")
    def test_ingest_empty_dir(
        self, mock_pipeline_cls: MagicMock, tmp_db: Database, tmp_path: Path
    ) -> None:
        epub_dir = tmp_path / "empty"
        epub_dir.mkdir()
        mock_pipeline_cls.return_value.ingest_directory.return_value = IngestionSummary(
            results=[]
        )

        app = create_app(db=tmp_db, settings=_settings_with_epub_dir(tmp_path))
        with TestClient(app) as client:
            resp = client.post("/api/v1/ingest", json={"epub_dir": "empty"})
            assert resp.status_code == 200
            assert resp.json()["total"] == 0

    @patch("litscope.ingestion.pipeline.IngestionPipeline")
    def test_ingest_with_skipped(
        self, mock_pipeline_cls: MagicMock, tmp_db: Database, tmp_path: Path
    ) -> None:
        epub_dir = tmp_path / "epubs"
        epub_dir.mkdir()
        mock_pipeline_cls.return_value.ingest_directory.return_value = IngestionSummary(
            results=[
                IngestionResult(
                    work_id="sample",
                    title="Sample",
                    success=True,
                    skipped=True,
                )
            ]
        )

        app = create_app(db=tmp_db, settings=_settings_with_epub_dir(tmp_path))
        with TestClient(app) as client:
            resp = client.post("/api/v1/ingest", json={"epub_dir": "epubs"})
            assert resp.status_code == 200
            assert resp.json()["skipped"] == 1

    @patch("litscope.ingestion.pipeline.IngestionPipeline")
    def test_ingest_with_failure(
        self, mock_pipeline_cls: MagicMock, tmp_db: Database, tmp_path: Path
    ) -> None:
        epub_dir = tmp_path / "epubs"
        epub_dir.mkdir()
        mock_pipeline_cls.return_value.ingest_directory.return_value = IngestionSummary(
            results=[
                IngestionResult(
                    work_id="bad",
                    title="Bad",
                    success=False,
                    error="parse error",
                )
            ]
        )

        app = create_app(db=tmp_db, settings=_settings_with_epub_dir(tmp_path))
        with TestClient(app) as client:
            resp = client.post("/api/v1/ingest", json={"epub_dir": "epubs"})
            assert resp.status_code == 200
            body = resp.json()
            assert body["failed"] == 1
            assert body["results"][0]["error"] == "parse error"


class TestPathTraversalRejection:
    """Verify that path traversal attacks are rejected."""

    def test_dotdot_rejected_by_schema(self) -> None:
        with pytest.raises(ValueError, match="must not contain"):
            IngestRequest(epub_dir="../etc/passwd")

    def test_absolute_path_rejected_by_schema(self) -> None:
        with pytest.raises(ValueError, match="must be relative"):
            IngestRequest(epub_dir="/etc/passwd")

    def test_dotdot_rejected_via_api(self, tmp_db: Database, tmp_path: Path) -> None:
        app = create_app(db=tmp_db, settings=_settings_with_epub_dir(tmp_path))
        with TestClient(app) as client:
            resp = client.post("/api/v1/ingest", json={"epub_dir": "../etc"})
            assert resp.status_code == 422

    def test_absolute_path_rejected_via_api(
        self, tmp_db: Database, tmp_path: Path
    ) -> None:
        app = create_app(db=tmp_db, settings=_settings_with_epub_dir(tmp_path))
        with TestClient(app) as client:
            resp = client.post("/api/v1/ingest", json={"epub_dir": "/etc/passwd"})
            assert resp.status_code == 422

    @patch("litscope.ingestion.pipeline.IngestionPipeline")
    def test_valid_subdir_accepted(
        self, mock_pipeline_cls: MagicMock, tmp_db: Database, tmp_path: Path
    ) -> None:
        subdir = tmp_path / "sub" / "dir"
        subdir.mkdir(parents=True)
        mock_pipeline_cls.return_value.ingest_directory.return_value = _make_summary(
            results=[]
        )

        app = create_app(db=tmp_db, settings=_settings_with_epub_dir(tmp_path))
        with TestClient(app) as client:
            resp = client.post("/api/v1/ingest", json={"epub_dir": "sub/dir"})
            assert resp.status_code == 200
