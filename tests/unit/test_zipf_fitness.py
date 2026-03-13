"""Tests for Zipf fitness analyzer."""

import pytest

from litscope.analysis.classical.vocabulary_frequency import VocabularyFrequencyAnalyzer
from litscope.analysis.classical.zipf_fitness import ZipfFitnessAnalyzer
from litscope.analysis.models import AnalysisContext, AnalysisResult, WorkData
from litscope.analysis.registry import AnalyzerRegistry
from litscope.config import LitScopeSettings
from litscope.storage.database import Database


@pytest.fixture(autouse=True)
def _clean_registry() -> None:  # type: ignore[misc]
    AnalyzerRegistry.clear()
    import importlib

    import litscope.analysis.classical.vocabulary_frequency as vf
    import litscope.analysis.classical.zipf_fitness as zf

    importlib.reload(vf)
    importlib.reload(zf)
    yield  # type: ignore[misc]
    AnalyzerRegistry.clear()


class TestZipfFitnessAnalyzer:
    def test_synthetic_zipf(self) -> None:
        """Synthetic Zipf distribution should give alpha ≈ -1, R² ≈ 1."""
        # Create perfect Zipf: freq(rank) = C / rank
        freqs = {f"word{i}": {"count": 1000 // i, "tf": 0.0} for i in range(1, 51)}
        ctx = AnalysisContext()
        ctx.set(
            "vocabulary_frequency",
            AnalysisResult(
                "vocabulary_frequency",
                "w1",
                {"total_types": 50.0, "total_tokens": 1000.0},
                {"frequencies": freqs},
            ),
        )
        # Need a minimal DB for the analyzer constructor
        db = Database(":memory:")
        db.connect()
        db.migrate()
        db.conn.execute(
            "INSERT INTO works (work_id, title, author, file_path, file_hash) "
            "VALUES (?, ?, ?, ?, ?)",
            ["w1", "T", "A", "/p", "h"],
        )
        wd = WorkData(work_id="w1", _db=db)
        analyzer = ZipfFitnessAnalyzer(db, LitScopeSettings())
        result = analyzer.analyze(wd, ctx)
        assert result.metrics["alpha"] == pytest.approx(-1.0, abs=0.1)
        assert result.metrics["r_squared"] == pytest.approx(1.0, abs=0.05)

    def test_real_data(self, seeded_db: Database, work_data: WorkData) -> None:
        settings = LitScopeSettings()
        ctx = AnalysisContext()
        vocab = VocabularyFrequencyAnalyzer(seeded_db, settings)
        ctx.set("vocabulary_frequency", vocab.analyze(work_data, ctx))
        analyzer = ZipfFitnessAnalyzer(seeded_db, settings)
        result = analyzer.analyze(work_data, ctx)
        assert "alpha" in result.metrics
        assert "r_squared" in result.metrics
        assert result.metrics["r_squared"] > 0

    def test_insufficient_data(self, tmp_db: Database) -> None:
        conn = tmp_db.conn
        conn.execute(
            "INSERT INTO works (work_id, title, author, file_path, file_hash) "
            "VALUES (?, ?, ?, ?, ?)",
            ["one-word", "T", "A", "/p", "h"],
        )
        ctx = AnalysisContext()
        ctx.set(
            "vocabulary_frequency",
            AnalysisResult(
                "vocabulary_frequency",
                "one-word",
                {"total_types": 1.0, "total_tokens": 1.0},
                {"frequencies": {"only": {"count": 1, "tf": 1.0}}},
            ),
        )
        wd = WorkData(work_id="one-word", _db=tmp_db)
        analyzer = ZipfFitnessAnalyzer(tmp_db, LitScopeSettings())
        result = analyzer.analyze(wd, ctx)
        assert result.metrics["alpha"] == 0.0
        assert result.metrics["r_squared"] == 0.0
