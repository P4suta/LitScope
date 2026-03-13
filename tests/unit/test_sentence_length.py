"""Tests for sentence length analyzer."""

import pytest

from litscope.analysis.classical.sentence_length import SentenceLengthAnalyzer
from litscope.analysis.models import AnalysisContext, WorkData
from litscope.analysis.registry import AnalyzerRegistry
from litscope.config import LitScopeSettings
from litscope.storage.database import Database


@pytest.fixture(autouse=True)
def _clean_registry() -> None:  # type: ignore[misc]
    AnalyzerRegistry.clear()
    import importlib

    import litscope.analysis.classical.sentence_length as mod

    importlib.reload(mod)
    yield  # type: ignore[misc]
    AnalyzerRegistry.clear()


class TestSentenceLengthAnalyzer:
    def test_mean(self, seeded_db: Database, work_data: WorkData) -> None:
        analyzer = SentenceLengthAnalyzer(seeded_db, LitScopeSettings())
        result = analyzer.analyze(work_data, AnalysisContext())
        # Sentences: 6, 6, 5 → mean = 17/3
        assert result.metrics["mean"] == pytest.approx(17 / 3)

    def test_median(self, seeded_db: Database, work_data: WorkData) -> None:
        analyzer = SentenceLengthAnalyzer(seeded_db, LitScopeSettings())
        result = analyzer.analyze(work_data, AnalysisContext())
        assert result.metrics["median"] == 6.0

    def test_stdev(self, seeded_db: Database, work_data: WorkData) -> None:
        analyzer = SentenceLengthAnalyzer(seeded_db, LitScopeSettings())
        result = analyzer.analyze(work_data, AnalysisContext())
        assert result.metrics["stdev"] > 0

    def test_min_max(self, seeded_db: Database, work_data: WorkData) -> None:
        analyzer = SentenceLengthAnalyzer(seeded_db, LitScopeSettings())
        result = analyzer.analyze(work_data, AnalysisContext())
        assert result.metrics["min"] == 5.0
        assert result.metrics["max"] == 6.0

    def test_empty_work(self, tmp_db: Database) -> None:
        conn = tmp_db.conn
        conn.execute(
            "INSERT INTO works (work_id, title, author, file_path, file_hash) "
            "VALUES (?, ?, ?, ?, ?)",
            ["empty-work", "Empty", "Author", "/path", "hash"],
        )
        wd = WorkData(work_id="empty-work", _db=tmp_db)
        analyzer = SentenceLengthAnalyzer(tmp_db, LitScopeSettings())
        result = analyzer.analyze(wd, AnalysisContext())
        assert result.metrics["mean"] == 0.0
