"""Tests for POS distribution analyzer."""

import pytest

from litscope.analysis.models import AnalysisContext, WorkData
from litscope.analysis.registry import AnalyzerRegistry
from litscope.analysis.syntactic.pos_distribution import PosDistributionAnalyzer
from litscope.config import LitScopeSettings
from litscope.storage.database import Database


@pytest.fixture(autouse=True)
def _clean_registry() -> None:  # type: ignore[misc]
    AnalyzerRegistry.clear()
    import importlib

    import litscope.analysis.syntactic.pos_distribution as mod

    importlib.reload(mod)
    yield  # type: ignore[misc]
    AnalyzerRegistry.clear()


class TestPosDistributionAnalyzer:
    def test_distribution(self, seeded_db: Database, work_data: WorkData) -> None:
        analyzer = PosDistributionAnalyzer(seeded_db, LitScopeSettings())
        result = analyzer.analyze(work_data, AnalysisContext())
        dist = result.data["distribution"]
        # DET: 4 (The x4), NOUN: 6 (cat x2, mat, dog, morning, sunlight), PUNCT: 3
        assert dist["DET"]["count"] == 4
        assert dist["NOUN"]["count"] == 6
        assert dist["PUNCT"]["count"] == 3

    def test_ratios_sum_to_one(self, seeded_db: Database, work_data: WorkData) -> None:
        analyzer = PosDistributionAnalyzer(seeded_db, LitScopeSettings())
        result = analyzer.analyze(work_data, AnalysisContext())
        dist = result.data["distribution"]
        total_ratio = sum(info["ratio"] for info in dist.values())
        assert total_ratio == pytest.approx(1.0)

    def test_metrics(self, seeded_db: Database, work_data: WorkData) -> None:
        analyzer = PosDistributionAnalyzer(seeded_db, LitScopeSettings())
        result = analyzer.analyze(work_data, AnalysisContext())
        assert result.metrics["total_tokens"] == 20.0

    def test_store_to_db(self, seeded_db: Database, work_data: WorkData) -> None:
        analyzer = PosDistributionAnalyzer(seeded_db, LitScopeSettings())
        result = analyzer.analyze(work_data, AnalysisContext())
        analyzer.store_result(result)
        rows = seeded_db.conn.execute(
            "SELECT pos, count, ratio FROM pos_distributions WHERE work_id = ?",
            ["test-work"],
        ).fetchall()
        assert len(rows) > 0
        pos_set = {r[0] for r in rows}
        assert "NOUN" in pos_set
        assert "VERB" in pos_set

    def test_empty_work(self, tmp_db: Database) -> None:
        conn = tmp_db.conn
        conn.execute(
            "INSERT INTO works (work_id, title, author, file_path, file_hash) "
            "VALUES (?, ?, ?, ?, ?)",
            ["empty-work", "E", "A", "/p", "h"],
        )
        wd = WorkData(work_id="empty-work", _db=tmp_db)
        analyzer = PosDistributionAnalyzer(tmp_db, LitScopeSettings())
        result = analyzer.analyze(wd, AnalysisContext())
        assert result.metrics["total_tokens"] == 0.0
        assert result.data["distribution"] == {}
