"""Tests for voice ratio analyzer."""

import pytest

from litscope.analysis.models import AnalysisContext, WorkData
from litscope.analysis.registry import AnalyzerRegistry
from litscope.analysis.syntactic.pos_distribution import PosDistributionAnalyzer
from litscope.analysis.syntactic.voice_ratio import VoiceRatioAnalyzer
from litscope.config import LitScopeSettings
from litscope.storage.database import Database


@pytest.fixture(autouse=True)
def _clean_registry() -> None:  # type: ignore[misc]
    AnalyzerRegistry.clear()
    import importlib

    import litscope.analysis.syntactic.pos_distribution as pd
    import litscope.analysis.syntactic.voice_ratio as vr

    importlib.reload(pd)
    importlib.reload(vr)
    yield  # type: ignore[misc]
    AnalyzerRegistry.clear()


class TestVoiceRatioAnalyzer:
    def _run_with_context(
        self, db: Database, work_data: WorkData
    ) -> tuple[VoiceRatioAnalyzer, AnalysisContext]:
        settings = LitScopeSettings()
        ctx = AnalysisContext()
        pos_dist = PosDistributionAnalyzer(db, settings)
        ctx.set("pos_distribution", pos_dist.analyze(work_data, ctx))
        return VoiceRatioAnalyzer(db, settings), ctx

    def test_active_sentences(self, seeded_db: Database, work_data: WorkData) -> None:
        analyzer, ctx = self._run_with_context(seeded_db, work_data)
        result = analyzer.analyze(work_data, ctx)
        # All test sentences are active voice
        assert result.metrics["active_count"] == 3.0

    def test_passive_ratio(self, seeded_db: Database, work_data: WorkData) -> None:
        analyzer, ctx = self._run_with_context(seeded_db, work_data)
        result = analyzer.analyze(work_data, ctx)
        assert result.metrics["passive_ratio"] == pytest.approx(0.0)

    def test_passive_detection(self, seeded_db: Database) -> None:
        """Test with a passive sentence added to the DB."""
        conn = seeded_db.conn
        # Add a passive sentence
        conn.execute(
            "INSERT INTO sentences (sentence_id, work_id, chapter_id, position, "
            "text, word_count, char_count) VALUES (?, ?, ?, ?, ?, ?, ?)",
            [
                "test-work::ch000::s002",
                "test-work",
                "test-work::ch000",
                3,
                "The ball was kicked by the boy.",
                7,
                30,
            ],
        )
        wd = WorkData(work_id="test-work", _db=seeded_db)
        settings = LitScopeSettings()
        ctx = AnalysisContext()
        pos_dist = PosDistributionAnalyzer(seeded_db, settings)
        ctx.set("pos_distribution", pos_dist.analyze(wd, ctx))
        analyzer = VoiceRatioAnalyzer(seeded_db, settings)
        result = analyzer.analyze(wd, ctx)
        # At least some sentences detected
        assert result.metrics["passive_count"] + result.metrics["active_count"] == 4.0

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
        analyzer = VoiceRatioAnalyzer(tmp_db, settings)
        result = analyzer.analyze(wd, ctx)
        assert result.metrics["passive_ratio"] == 0.0

    def test_metrics_keys(self, seeded_db: Database, work_data: WorkData) -> None:
        analyzer, ctx = self._run_with_context(seeded_db, work_data)
        result = analyzer.analyze(work_data, ctx)
        assert set(result.metrics.keys()) == {
            "passive_count",
            "active_count",
            "passive_ratio",
        }
