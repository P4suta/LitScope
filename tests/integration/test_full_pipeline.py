"""Integration tests for the full LitScope pipeline."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from litscope.api.app import create_app
from litscope.config import LitScopeSettings
from litscope.storage.database import Database
from tests.conftest import create_sample_epub

pytestmark = pytest.mark.integration


def _ensure_registry() -> None:
    """Ensure all analyzers are registered (handles post-clear state)."""
    from litscope.analysis.registry import AnalyzerRegistry

    if not AnalyzerRegistry.all_names():
        # Modules already imported but registry cleared by unit tests.
        # Re-register by reloading analyzer modules.
        import importlib
        import pkgutil

        import litscope.analysis as pkg

        for _importer, modname, _ispkg in pkgutil.walk_packages(
            pkg.__path__, prefix=pkg.__name__ + "."
        ):
            if modname != "litscope.analysis.registry":
                importlib.reload(importlib.import_module(modname))
    else:
        AnalyzerRegistry.discover()


def _ingest_and_analyze(
    db: Database,
    epub_dir: Path,
    analyzers: list[str] | None = None,
) -> None:
    """Run ingestion and analysis pipeline on a directory."""
    from litscope.analysis.orchestrator import PipelineOrchestrator
    from litscope.config import LitScopeSettings
    from litscope.ingestion.pipeline import IngestionPipeline

    pipeline = IngestionPipeline(db=db)
    pipeline.ingest_directory(epub_dir)

    _ensure_registry()
    settings = LitScopeSettings()
    orchestrator = PipelineOrchestrator(db, settings)
    orchestrator.run_all_works(analyzers)


class TestIngestThenQuery:
    def test_ingest_then_query_works_api(self, tmp_path: Path) -> None:
        """POST /ingest → GET /works returns the ingested work."""
        epub_dir = tmp_path / "epubs"
        epub_dir.mkdir()
        create_sample_epub(epub_dir)

        db_path = tmp_path / "test.duckdb"
        settings = LitScopeSettings(db_path=db_path)
        app = create_app(settings=settings)

        with TestClient(app) as client:
            resp = client.post(
                "/api/v1/ingest",
                json={"epub_dir": str(epub_dir)},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["ingested"] >= 1

            resp = client.get("/api/v1/works")
            assert resp.status_code == 200
            works = resp.json()
            assert works["total"] >= 1
            assert len(works["items"]) >= 1


class TestIngestAnalyzeQuery:
    def test_ingest_analyze_vocabulary_api(self, tmp_path: Path) -> None:
        """Full pipeline → GET /works/{id}/vocabulary returns results."""
        epub_dir = tmp_path / "epubs"
        epub_dir.mkdir()
        create_sample_epub(epub_dir)

        db_path = tmp_path / "test.duckdb"
        db = Database(db_path)
        db.connect()
        db.migrate()

        _ingest_and_analyze(db, epub_dir, ["vocabulary_frequency", "lexical_richness"])

        work_id = db.conn.execute("SELECT work_id FROM works LIMIT 1").fetchone()[0]

        settings = LitScopeSettings(db_path=db_path)
        app = create_app(db=db, settings=settings)
        with TestClient(app) as client:
            resp = client.get(f"/api/v1/works/{work_id}/vocabulary")
            assert resp.status_code == 200
            data = resp.json()
            assert data["total_tokens"] > 0
            assert data["unique_lemmas"] > 0
            assert len(data["top_words"]) > 0

    def test_ingest_analyze_syntax_api(self, tmp_path: Path) -> None:
        """Full pipeline → GET /works/{id}/syntax returns results."""
        epub_dir = tmp_path / "epubs"
        epub_dir.mkdir()
        create_sample_epub(epub_dir)

        db_path = tmp_path / "test.duckdb"
        db = Database(db_path)
        db.connect()
        db.migrate()

        _ingest_and_analyze(
            db,
            epub_dir,
            [
                "vocabulary_frequency",
                "pos_distribution",
                "pos_transition",
                "sentence_openings",
                "voice_ratio",
            ],
        )

        work_id = db.conn.execute("SELECT work_id FROM works LIMIT 1").fetchone()[0]

        settings = LitScopeSettings(db_path=db_path)
        app = create_app(db=db, settings=settings)
        with TestClient(app) as client:
            resp = client.get(f"/api/v1/works/{work_id}/syntax")
            assert resp.status_code == 200
            data = resp.json()
            assert len(data["pos_distribution"]) > 0

    def test_ingest_compare_api(self, tmp_path: Path) -> None:
        """Ingest 2 works → GET /compare returns comparison."""
        epub_dir1 = tmp_path / "epubs1"
        epub_dir1.mkdir()
        create_sample_epub(epub_dir1)

        epub_dir2 = tmp_path / "epubs2"
        epub_dir2.mkdir()
        # Create second EPUB with different content
        from ebooklib import epub

        book = epub.EpubBook()
        book.set_identifier(
            "https://standardebooks.org/ebooks/another-author/another-title"
        )
        book.set_title("Another Title")
        book.set_language("en")
        book.add_author("Another Author")
        book.add_metadata("DC", "date", "1950-01-01")
        book.add_metadata("DC", "subject", "Fiction")

        ch = epub.EpubHtml(title="Chapter 1", file_name="chapter-1.xhtml")
        ch.set_content(
            b"<html><body><section>"
            b"<h2>Chapter 1</h2>"
            b"<p>A completely different story begins here.</p>"
            b"</section></body></html>"
        )
        book.add_item(ch)
        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())
        book.spine = [ch]
        epub.write_epub(str(epub_dir2 / "another.epub"), book)

        db_path = tmp_path / "test.duckdb"
        db = Database(db_path)
        db.connect()
        db.migrate()

        _ingest_and_analyze(db, epub_dir1, ["vocabulary_frequency"])
        _ingest_and_analyze(db, epub_dir2, ["vocabulary_frequency"])

        work_ids = [
            r[0] for r in db.conn.execute("SELECT work_id FROM works").fetchall()
        ]
        assert len(work_ids) >= 2

        settings = LitScopeSettings(db_path=db_path)
        app = create_app(db=db, settings=settings)
        with TestClient(app) as client:
            resp = client.get(
                "/api/v1/compare",
                params=[("work_id", wid) for wid in work_ids[:2]],
            )
            assert resp.status_code == 200
            data = resp.json()
            assert len(data) == 2


class TestErrorPaths:
    def test_ingest_file_not_found_returns_400(
        self, integration_client: TestClient
    ) -> None:
        """POST /ingest with non-existent directory returns 400."""
        resp = integration_client.post(
            "/api/v1/ingest",
            json={"epub_dir": "/nonexistent/path"},
        )
        assert resp.status_code == 400

    def test_work_not_found_returns_404(self, integration_client: TestClient) -> None:
        """GET /works/{id} for non-existent work returns 404."""
        resp = integration_client.get("/api/v1/works/nonexistent-id")
        assert resp.status_code == 404
