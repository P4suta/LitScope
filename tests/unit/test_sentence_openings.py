"""Tests for sentence openings analyzer."""

import pytest

from litscope.analysis.models import AnalysisContext, WorkData
from litscope.analysis.registry import AnalyzerRegistry
from litscope.analysis.syntactic.pos_distribution import PosDistributionAnalyzer
from litscope.analysis.syntactic.sentence_openings import SentenceOpeningsAnalyzer
from litscope.config import LitScopeSettings
from litscope.storage.database import Database


@pytest.fixture(autouse=True)
def _clean_registry() -> None:  # type: ignore[misc]
    AnalyzerRegistry.clear()
    import importlib

    import litscope.analysis.syntactic.pos_distribution as pd
    import litscope.analysis.syntactic.sentence_openings as so

    importlib.reload(pd)
    importlib.reload(so)
    yield  # type: ignore[misc]
    AnalyzerRegistry.clear()


class TestSentenceOpeningsAnalyzer:
    def _run_with_context(
        self, db: Database, work_data: WorkData
    ) -> tuple[SentenceOpeningsAnalyzer, AnalysisContext]:
        settings = LitScopeSettings()
        ctx = AnalysisContext()
        pos_dist = PosDistributionAnalyzer(db, settings)
        ctx.set("pos_distribution", pos_dist.analyze(work_data, ctx))
        return SentenceOpeningsAnalyzer(db, settings), ctx

    def test_patterns_exist(self, seeded_db: Database, work_data: WorkData) -> None:
        analyzer, ctx = self._run_with_context(seeded_db, work_data)
        result = analyzer.analyze(work_data, ctx)
        patterns = result.data["patterns"]
        # "DET" should appear as a unigram opening (2 of 3 sentences start with "The")
        assert "DET" in patterns
        assert patterns["DET"]["count"] == 2

    def test_trigram_patterns(self, seeded_db: Database, work_data: WorkData) -> None:
        analyzer, ctx = self._run_with_context(seeded_db, work_data)
        result = analyzer.analyze(work_data, ctx)
        patterns = result.data["patterns"]
        # "DET NOUN VERB" should appear (The cat sat, The dog chased)
        assert "DET NOUN VERB" in patterns

    def test_total_sentences(self, seeded_db: Database, work_data: WorkData) -> None:
        analyzer, ctx = self._run_with_context(seeded_db, work_data)
        result = analyzer.analyze(work_data, ctx)
        assert result.metrics["total_sentences"] == 3.0

    def test_store_to_db(self, seeded_db: Database, work_data: WorkData) -> None:
        analyzer, ctx = self._run_with_context(seeded_db, work_data)
        result = analyzer.analyze(work_data, ctx)
        analyzer.store_result(result)
        rows = seeded_db.conn.execute(
            "SELECT pattern, count FROM sentence_opening_patterns WHERE work_id = ?",
            ["test-work"],
        ).fetchall()
        assert len(rows) > 0

    def test_empty_work(self, tmp_db: Database) -> None:
        conn = tmp_db.conn
        conn.execute(
            "INSERT INTO works (work_id, title, author, file_path, file_hash) "
            "VALUES (?, ?, ?, ?, ?)",
            ["empty-work", "E", "A", "/p", "h"],
        )
        wd = WorkData(work_id="empty-work", _db=tmp_db)
        settings = LitScopeSettings()
        ctx = AnalysisContext()
        pos_dist = PosDistributionAnalyzer(tmp_db, settings)
        ctx.set("pos_distribution", pos_dist.analyze(wd, ctx))
        analyzer = SentenceOpeningsAnalyzer(tmp_db, settings)
        result = analyzer.analyze(wd, ctx)
        assert result.metrics["total_sentences"] == 0.0
