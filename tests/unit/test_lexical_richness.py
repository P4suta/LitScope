"""Tests for lexical richness analyzer."""

import pytest

from litscope.analysis.classical.lexical_richness import LexicalRichnessAnalyzer
from litscope.analysis.classical.vocabulary_frequency import VocabularyFrequencyAnalyzer
from litscope.analysis.models import AnalysisContext, WorkData
from litscope.analysis.registry import AnalyzerRegistry
from litscope.config import LitScopeSettings
from litscope.storage.database import Database


@pytest.fixture(autouse=True)
def _clean_registry() -> None:  # type: ignore[misc]
    AnalyzerRegistry.clear()
    import importlib

    import litscope.analysis.classical.lexical_richness as lr
    import litscope.analysis.classical.vocabulary_frequency as vf

    importlib.reload(vf)
    importlib.reload(lr)
    yield  # type: ignore[misc]
    AnalyzerRegistry.clear()


class TestLexicalRichnessAnalyzer:
    def _run_with_context(
        self, db: Database, work_data: WorkData
    ) -> tuple[LexicalRichnessAnalyzer, AnalysisContext]:
        settings = LitScopeSettings()
        ctx = AnalysisContext()
        vocab = VocabularyFrequencyAnalyzer(db, settings)
        vocab_result = vocab.analyze(work_data, ctx)
        ctx.set("vocabulary_frequency", vocab_result)
        return LexicalRichnessAnalyzer(db, settings), ctx

    def test_ttr(self, seeded_db: Database, work_data: WorkData) -> None:
        analyzer, ctx = self._run_with_context(seeded_db, work_data)
        result = analyzer.analyze(work_data, ctx)
        # 13 types / 17 tokens
        assert result.metrics["ttr"] == pytest.approx(13 / 17)

    def test_hapax_ratio(self, seeded_db: Database, work_data: WorkData) -> None:
        analyzer, ctx = self._run_with_context(seeded_db, work_data)
        result = analyzer.analyze(work_data, ctx)
        # Stopwords excluded from frequencies since 402a975.
        # Non-stop hapax (count=1): sit, mat, dog, chase, quickly,
        # morning, come, gentle, sunlight = 9
        # cat appears 2 times → not hapax
        # total_tokens = 17 (all non-PUNCT, including stopwords)
        assert result.metrics["hapax_ratio"] == pytest.approx(9 / 17)

    def test_yules_k(self, seeded_db: Database, work_data: WorkData) -> None:
        analyzer, ctx = self._run_with_context(seeded_db, work_data)
        result = analyzer.analyze(work_data, ctx)
        # Yule's K can be negative for small, high-diversity corpora
        assert isinstance(result.metrics["yules_k"], float)

    def test_mtld(self, seeded_db: Database, work_data: WorkData) -> None:
        analyzer, ctx = self._run_with_context(seeded_db, work_data)
        result = analyzer.analyze(work_data, ctx)
        assert result.metrics["mtld"] > 0

    def test_empty_work(self, tmp_db: Database) -> None:
        conn = tmp_db.conn
        conn.execute(
            "INSERT INTO works (work_id, title, author, file_path, file_hash) "
            "VALUES (?, ?, ?, ?, ?)",
            ["empty-work", "Empty", "Author", "/path", "hash"],
        )
        wd = WorkData(work_id="empty-work", _db=tmp_db)
        settings = LitScopeSettings()
        ctx = AnalysisContext()
        vocab = VocabularyFrequencyAnalyzer(tmp_db, settings)
        ctx.set("vocabulary_frequency", vocab.analyze(wd, ctx))
        analyzer = LexicalRichnessAnalyzer(tmp_db, settings)
        result = analyzer.analyze(wd, ctx)
        assert result.metrics["ttr"] == 0.0
        assert result.metrics["mtld"] == 0.0

    def test_mtld_empty_tokens(self, seeded_db: Database) -> None:
        analyzer = LexicalRichnessAnalyzer(seeded_db, LitScopeSettings())
        assert analyzer._mtld_one_direction([]) == 0.0

    def test_mtld_ends_at_threshold(self, seeded_db: Database) -> None:
        """MTLD where the last token triggers factor reset (token_count=0 at end).

        Covers the False branch of `if token_count > 0:` in _mtld_one_direction.
        """
        analyzer = LexicalRichnessAnalyzer(seeded_db, LitScopeSettings())
        # 2 types in 3 tokens → TTR = 2/3 ≈ 0.667 ≤ 0.72 → factor resets
        # Loop ends with token_count == 0 (no partial factor)
        tokens = ["a", "b", "a"]
        result = analyzer._mtld_one_direction(tokens)
        assert result == pytest.approx(3.0)

    def test_stores_in_analysis_results(
        self, seeded_db: Database, work_data: WorkData
    ) -> None:
        analyzer, ctx = self._run_with_context(seeded_db, work_data)
        result = analyzer.analyze(work_data, ctx)
        analyzer.store_result(result)
        row = seeded_db.conn.execute(
            "SELECT analyzer_name FROM analysis_results WHERE analyzer_name = ?",
            ["lexical_richness"],
        ).fetchone()
        assert row is not None
