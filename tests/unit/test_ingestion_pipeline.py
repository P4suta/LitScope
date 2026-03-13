"""Tests for ingestion pipeline."""

from pathlib import Path

import pytest
from ebooklib import epub

from litscope.ingestion.pipeline import IngestionPipeline, IngestionSummary
from litscope.ingestion.text_normalizer import TextNormalizer
from litscope.storage.database import Database
from tests.conftest import create_sample_epub


@pytest.fixture
def db() -> Database:
    d = Database(":memory:")
    d.connect()
    d.migrate()
    return d


@pytest.fixture
def epub_dir(tmp_path: Path) -> Path:
    create_sample_epub(tmp_path)
    return tmp_path


@pytest.fixture
def pipeline(db: Database) -> IngestionPipeline:
    return IngestionPipeline(db=db)


class TestIngestionPipeline:
    def test_ingest_directory(
        self, pipeline: IngestionPipeline, epub_dir: Path
    ) -> None:
        summary = pipeline.ingest_directory(epub_dir)
        assert summary.total == 1
        assert summary.ingested == 1
        assert summary.failed == 0

    def test_work_inserted(
        self, pipeline: IngestionPipeline, epub_dir: Path, db: Database
    ) -> None:
        pipeline.ingest_directory(epub_dir)
        row = db.conn.execute("SELECT COUNT(*) FROM works").fetchone()
        assert row is not None
        assert row[0] == 1

    def test_chapters_inserted(
        self, pipeline: IngestionPipeline, epub_dir: Path, db: Database
    ) -> None:
        pipeline.ingest_directory(epub_dir)
        row = db.conn.execute("SELECT COUNT(*) FROM chapters").fetchone()
        assert row is not None
        assert row[0] == 2

    def test_sentences_inserted(
        self, pipeline: IngestionPipeline, epub_dir: Path, db: Database
    ) -> None:
        pipeline.ingest_directory(epub_dir)
        row = db.conn.execute("SELECT COUNT(*) FROM sentences").fetchone()
        assert row is not None
        assert row[0] > 0

    def test_tokens_inserted(
        self, pipeline: IngestionPipeline, epub_dir: Path, db: Database
    ) -> None:
        pipeline.ingest_directory(epub_dir)
        row = db.conn.execute("SELECT COUNT(*) FROM tokens").fetchone()
        assert row is not None
        assert row[0] > 0

    def test_work_id_from_stem(
        self, pipeline: IngestionPipeline, epub_dir: Path, db: Database
    ) -> None:
        pipeline.ingest_directory(epub_dir)
        row = db.conn.execute("SELECT work_id FROM works").fetchone()
        assert row is not None
        assert row[0] == "sample"

    def test_chapter_ids_hierarchical(
        self, pipeline: IngestionPipeline, epub_dir: Path, db: Database
    ) -> None:
        pipeline.ingest_directory(epub_dir)
        rows = db.conn.execute(
            "SELECT chapter_id FROM chapters ORDER BY position"
        ).fetchall()
        assert rows[0][0] == "sample::ch000"
        assert rows[1][0] == "sample::ch001"

    def test_sentence_ids_hierarchical(
        self, pipeline: IngestionPipeline, epub_dir: Path, db: Database
    ) -> None:
        pipeline.ingest_directory(epub_dir)
        row = db.conn.execute(
            "SELECT sentence_id FROM sentences ORDER BY position LIMIT 1"
        ).fetchone()
        assert row is not None
        assert row[0].startswith("sample::ch000::s")


class TestDifferentialIngestion:
    def test_skip_unchanged(self, pipeline: IngestionPipeline, epub_dir: Path) -> None:
        pipeline.ingest_directory(epub_dir)
        summary = pipeline.ingest_directory(epub_dir)
        assert summary.skipped == 1
        assert summary.ingested == 0

    def test_reingestion_on_change(
        self, pipeline: IngestionPipeline, epub_dir: Path, db: Database
    ) -> None:
        pipeline.ingest_directory(epub_dir)
        # Modify the epub to change its hash
        epub_path = epub_dir / "sample.epub"
        _create_modified_epub(epub_path)
        summary = pipeline.ingest_directory(epub_dir)
        assert summary.ingested == 1
        assert summary.skipped == 0


class TestErrorIsolation:
    def test_bad_file_does_not_stop_batch(self, db: Database, tmp_path: Path) -> None:
        # Create a bad file and a good file
        (tmp_path / "bad.epub").write_bytes(b"not an epub")
        create_sample_epub(tmp_path)
        pipeline = IngestionPipeline(db=db)
        summary = pipeline.ingest_directory(tmp_path)
        assert summary.total == 2
        assert summary.failed == 1
        assert summary.ingested == 1

    def test_failed_result_has_error(self, db: Database, tmp_path: Path) -> None:
        (tmp_path / "bad.epub").write_bytes(b"not an epub")
        pipeline = IngestionPipeline(db=db)
        summary = pipeline.ingest_directory(tmp_path)
        failed = [r for r in summary.results if not r.success]
        assert len(failed) == 1
        assert failed[0].error is not None


class TestIngestionSummary:
    def test_empty_summary(self) -> None:
        summary = IngestionSummary()
        assert summary.total == 0
        assert summary.ingested == 0
        assert summary.skipped == 0
        assert summary.failed == 0


class TestEmptyTokenSentence:
    def test_sentence_with_no_tokens(self, db: Database, tmp_path: Path) -> None:
        """Sentences with empty tokens list should be stored without token inserts."""
        from unittest.mock import patch

        from litscope.ingestion.text_normalizer import (
            NormalizedChapter,
            NormalizedSentence,
        )

        create_sample_epub(tmp_path)
        # Return a chapter with one sentence that has no tokens
        empty_chapter = NormalizedChapter(
            sentences=[NormalizedSentence(text="...", tokens=[])]
        )

        with patch.object(TextNormalizer, "normalize", return_value=empty_chapter):
            pipeline = IngestionPipeline(db=db)
            summary = pipeline.ingest_directory(tmp_path)

        assert summary.ingested == 1
        result = next(r for r in summary.results if r.success and not r.skipped)
        assert result.tokens == 0
        # Sentences should still be inserted
        row = db.conn.execute("SELECT COUNT(*) FROM sentences").fetchone()
        assert row is not None
        assert row[0] > 0
        # But no tokens
        row = db.conn.execute("SELECT COUNT(*) FROM tokens").fetchone()
        assert row is not None
        assert row[0] == 0


class TestIngestFile:
    def test_ingest_file_success(self, db: Database, epub_dir: Path) -> None:
        pipeline = IngestionPipeline(db=db)
        result = pipeline.ingest_file(epub_dir / "sample.epub")
        assert result.success is True
        assert result.chapters > 0
        assert result.tokens > 0

    def test_ingest_file_error_isolation(self, db: Database, tmp_path: Path) -> None:
        bad_file = tmp_path / "bad.epub"
        bad_file.write_bytes(b"not an epub")
        pipeline = IngestionPipeline(db=db)
        result = pipeline.ingest_file(bad_file)
        assert result.success is False
        assert result.error is not None


class TestEmptyDirectory:
    def test_no_epubs(self, pipeline: IngestionPipeline, tmp_path: Path) -> None:
        summary = pipeline.ingest_directory(tmp_path)
        assert summary.total == 0


def _create_modified_epub(path: Path) -> None:
    """Create a different EPUB at the same path to simulate a changed file."""
    book = epub.EpubBook()
    book.set_identifier("https://standardebooks.org/ebooks/test-author/test-title")
    book.set_title("Test Title Modified")
    book.set_language("en")
    book.add_author("Test Author")
    book.add_metadata("DC", "date", "1920-01-01")
    ch1 = epub.EpubHtml(title="Chapter 1", file_name="chapter-1.xhtml")
    ch1.set_content(
        b"<html><body><section><h2>Chapter 1</h2>"
        b"<p>Completely new content here.</p></section></body></html>"
    )
    book.add_item(ch1)
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = [ch1]
    epub.write_epub(str(path), book)
