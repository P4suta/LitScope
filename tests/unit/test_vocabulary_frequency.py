"""Tests for vocabulary frequency analyzer."""

import pytest

from litscope.analysis.classical.vocabulary_frequency import VocabularyFrequencyAnalyzer
from litscope.analysis.models import AnalysisContext, WorkData
from litscope.analysis.registry import AnalyzerRegistry
from litscope.config import LitScopeSettings
from litscope.storage.database import Database


@pytest.fixture(autouse=True)
def _clean_registry() -> None:  # type: ignore[misc]
    AnalyzerRegistry.clear()
    # Re-import to re-register
    import importlib

    import litscope.analysis.classical.vocabulary_frequency as mod

    importlib.reload(mod)
    yield  # type: ignore[misc]
    AnalyzerRegistry.clear()


class TestVocabularyFrequencyAnalyzer:
    def test_correct_tf(self, seeded_db: Database, work_data: WorkData) -> None:
        analyzer = VocabularyFrequencyAnalyzer(seeded_db, LitScopeSettings())
        result = analyzer.analyze(work_data, AnalysisContext())
        freqs = result.data["frequencies"]
        # "the" appears 4 times (lemma "the"), total non-PUNCT tokens = 17
        assert freqs["the"]["count"] == 4
        assert freqs["the"]["tf"] == pytest.approx(4 / 17)

    def test_ranking(self, seeded_db: Database, work_data: WorkData) -> None:
        analyzer = VocabularyFrequencyAnalyzer(seeded_db, LitScopeSettings())
        result = analyzer.analyze(work_data, AnalysisContext())
        freqs = result.data["frequencies"]
        lemmas = list(freqs.keys())
        counts = [freqs[lemma]["count"] for lemma in lemmas]
        assert counts == sorted(counts, reverse=True)

    def test_metrics(self, seeded_db: Database, work_data: WorkData) -> None:
        analyzer = VocabularyFrequencyAnalyzer(seeded_db, LitScopeSettings())
        result = analyzer.analyze(work_data, AnalysisContext())
        assert result.metrics["total_tokens"] == 17.0
        # 13 unique lemmas
        assert result.metrics["total_types"] == 13.0

    def test_excludes_punct(self, seeded_db: Database, work_data: WorkData) -> None:
        analyzer = VocabularyFrequencyAnalyzer(seeded_db, LitScopeSettings())
        result = analyzer.analyze(work_data, AnalysisContext())
        assert "." not in result.data["frequencies"]

    def test_store_to_db(self, seeded_db: Database, work_data: WorkData) -> None:
        analyzer = VocabularyFrequencyAnalyzer(seeded_db, LitScopeSettings())
        result = analyzer.analyze(work_data, AnalysisContext())
        analyzer.store_result(result)

        rows = seeded_db.conn.execute(
            "SELECT lemma, count, tf FROM word_frequencies WHERE work_id = ? "
            "ORDER BY count DESC",
            ["test-work"],
        ).fetchall()
        assert len(rows) == 13
        assert rows[0][0] == "the"
        assert rows[0][1] == 4

    def test_empty_work(self, tmp_db: Database) -> None:
        conn = tmp_db.conn
        conn.execute(
            "INSERT INTO works (work_id, title, author, file_path, file_hash) "
            "VALUES (?, ?, ?, ?, ?)",
            ["empty-work", "Empty", "Author", "/path", "hash"],
        )
        wd = WorkData(work_id="empty-work", _db=tmp_db)
        analyzer = VocabularyFrequencyAnalyzer(tmp_db, LitScopeSettings())
        result = analyzer.analyze(wd, AnalysisContext())
        assert result.metrics["total_tokens"] == 0.0
        assert result.metrics["total_types"] == 0.0
        assert result.data["frequencies"] == {}
