"""Tests for POS transition analyzer."""

import pytest

from litscope.analysis.models import AnalysisContext, WorkData
from litscope.analysis.registry import AnalyzerRegistry
from litscope.analysis.syntactic.pos_distribution import PosDistributionAnalyzer
from litscope.analysis.syntactic.pos_transition import PosTransitionAnalyzer
from litscope.config import LitScopeSettings
from litscope.storage.database import Database


@pytest.fixture(autouse=True)
def _clean_registry() -> None:  # type: ignore[misc]
    AnalyzerRegistry.clear()
    import importlib

    import litscope.analysis.syntactic.pos_distribution as pd
    import litscope.analysis.syntactic.pos_transition as pt

    importlib.reload(pd)
    importlib.reload(pt)
    yield  # type: ignore[misc]
    AnalyzerRegistry.clear()


class TestPosTransitionAnalyzer:
    def _run_with_context(
        self, db: Database, work_data: WorkData
    ) -> tuple[PosTransitionAnalyzer, AnalysisContext]:
        settings = LitScopeSettings()
        ctx = AnalysisContext()
        pos_dist = PosDistributionAnalyzer(db, settings)
        ctx.set("pos_distribution", pos_dist.analyze(work_data, ctx))
        return PosTransitionAnalyzer(db, settings), ctx

    def test_transitions_exist(self, seeded_db: Database, work_data: WorkData) -> None:
        analyzer, ctx = self._run_with_context(seeded_db, work_data)
        result = analyzer.analyze(work_data, ctx)
        transitions = result.data["transitions"]
        # DET->NOUN should exist (The cat, The dog, the mat, the cat)
        assert "DET->NOUN" in transitions
        assert transitions["DET->NOUN"]["count"] >= 3

    def test_ratios_sum_to_one(self, seeded_db: Database, work_data: WorkData) -> None:
        analyzer, ctx = self._run_with_context(seeded_db, work_data)
        result = analyzer.analyze(work_data, ctx)
        transitions = result.data["transitions"]
        total = sum(t["ratio"] for t in transitions.values())
        assert total == pytest.approx(1.0)

    def test_within_sentence_only(
        self, seeded_db: Database, work_data: WorkData
    ) -> None:
        """Transitions should not cross sentence boundaries."""
        analyzer, ctx = self._run_with_context(seeded_db, work_data)
        result = analyzer.analyze(work_data, ctx)
        # Total transitions = (7-1) + (7-1) + (6-1) = 17
        assert result.metrics["total_transitions"] == 17.0

    def test_store_to_db(self, seeded_db: Database, work_data: WorkData) -> None:
        analyzer, ctx = self._run_with_context(seeded_db, work_data)
        result = analyzer.analyze(work_data, ctx)
        analyzer.store_result(result)
        rows = seeded_db.conn.execute(
            "SELECT from_pos, to_pos, count FROM pos_transitions WHERE work_id = ?",
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
        analyzer = PosTransitionAnalyzer(tmp_db, settings)
        result = analyzer.analyze(wd, ctx)
        assert result.metrics["total_transitions"] == 0.0
