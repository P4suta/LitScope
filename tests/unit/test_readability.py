"""Tests for readability analyzer."""

import pytest

from litscope.analysis.classical.readability import ReadabilityAnalyzer
from litscope.analysis.models import AnalysisContext, WorkData
from litscope.analysis.registry import AnalyzerRegistry
from litscope.config import LitScopeSettings
from litscope.storage.database import Database


@pytest.fixture(autouse=True)
def _clean_registry() -> None:  # type: ignore[misc]
    AnalyzerRegistry.clear()
    import importlib

    import litscope.analysis.classical.readability as mod

    importlib.reload(mod)
    yield  # type: ignore[misc]
    AnalyzerRegistry.clear()


class TestReadabilityAnalyzer:
    def test_flesch_kincaid(self, seeded_db: Database, work_data: WorkData) -> None:
        analyzer = ReadabilityAnalyzer(seeded_db, LitScopeSettings())
        result = analyzer.analyze(work_data, AnalysisContext())
        # Simple sentences should give a low (easy) grade level
        assert isinstance(result.metrics["flesch_kincaid"], float)

    def test_coleman_liau(self, seeded_db: Database, work_data: WorkData) -> None:
        analyzer = ReadabilityAnalyzer(seeded_db, LitScopeSettings())
        result = analyzer.analyze(work_data, AnalysisContext())
        assert isinstance(result.metrics["coleman_liau"], float)

    def test_ari(self, seeded_db: Database, work_data: WorkData) -> None:
        analyzer = ReadabilityAnalyzer(seeded_db, LitScopeSettings())
        result = analyzer.analyze(work_data, AnalysisContext())
        assert isinstance(result.metrics["ari"], float)

    def test_all_three_keys(self, seeded_db: Database, work_data: WorkData) -> None:
        analyzer = ReadabilityAnalyzer(seeded_db, LitScopeSettings())
        result = analyzer.analyze(work_data, AnalysisContext())
        assert set(result.metrics.keys()) == {"flesch_kincaid", "coleman_liau", "ari"}

    def test_empty_work(self, tmp_db: Database) -> None:
        conn = tmp_db.conn
        conn.execute(
            "INSERT INTO works (work_id, title, author, file_path, file_hash) "
            "VALUES (?, ?, ?, ?, ?)",
            ["empty-work", "Empty", "Author", "/path", "hash"],
        )
        wd = WorkData(work_id="empty-work", _db=tmp_db)
        analyzer = ReadabilityAnalyzer(tmp_db, LitScopeSettings())
        result = analyzer.analyze(wd, AnalysisContext())
        assert result.metrics["flesch_kincaid"] == 0.0
        assert result.metrics["coleman_liau"] == 0.0
        assert result.metrics["ari"] == 0.0
