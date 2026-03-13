"""Tests for pipeline benchmark, orchestrator timing, skip logic, and parallelism."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, ClassVar

import pytest

from litscope.analysis.base import BaseAnalyzer
from litscope.analysis.models import AnalysisContext, AnalysisResult, WorkData
from litscope.analysis.orchestrator import (
    AnalyzerTiming,
    PipelineOrchestrator,
    _build_layers,
)
from litscope.analysis.registry import AnalyzerRegistry
from litscope.cli.benchmark import (
    AnalyzerSummary,
    BenchmarkResult,
    PipelineBenchmark,
    WorkSummary,
    format_csv,
    format_json,
    format_table,
)
from litscope.config import LitScopeSettings

if TYPE_CHECKING:
    from litscope.storage.database import Database


@pytest.fixture(autouse=True)
def _clean_registry() -> None:  # type: ignore[misc]
    saved = dict(AnalyzerRegistry._analyzers)
    AnalyzerRegistry.clear()
    yield  # type: ignore[misc]
    AnalyzerRegistry._analyzers.clear()
    AnalyzerRegistry._analyzers.update(saved)


# --- Phase A: Timing ---


class TestAnalyzerTiming:
    def test_fields(self) -> None:
        t = AnalyzerTiming("vocab", "work-1", 1.5, 0.3, 1.8)
        assert t.analyzer_name == "vocab"
        assert t.work_id == "work-1"
        assert t.analyze_seconds == 1.5
        assert t.store_seconds == 0.3
        assert t.total_seconds == 1.8

    def test_frozen(self) -> None:
        t = AnalyzerTiming("vocab", "work-1", 1.5, 0.3, 1.8)
        with pytest.raises(AttributeError):
            t.analyzer_name = "other"  # type: ignore[misc]


class TestOrchestratorTiming:
    def test_run_records_timings(self, seeded_db: Database) -> None:
        class TimedAnalyzer(BaseAnalyzer):
            name: ClassVar[str] = "timed"

            def analyze(
                self, work_data: WorkData, context: AnalysisContext
            ) -> AnalysisResult:
                return AnalysisResult(self.name, work_data.work_id, {"v": 1.0}, {})

        orchestrator = PipelineOrchestrator(seeded_db, LitScopeSettings())
        results = orchestrator.run("test-work", force=True)
        assert len(results) == 1
        assert len(orchestrator._last_timings) == 1

        t = orchestrator._last_timings[0]
        assert t.analyzer_name == "timed"
        assert t.work_id == "test-work"
        assert t.analyze_seconds >= 0
        assert t.store_seconds >= 0
        assert t.total_seconds >= t.analyze_seconds

    def test_run_all_works_accumulates_timings(self, seeded_db: Database) -> None:
        class AllTimedAnalyzer(BaseAnalyzer):
            name: ClassVar[str] = "all_timed"

            def analyze(
                self, work_data: WorkData, context: AnalysisContext
            ) -> AnalysisResult:
                return AnalysisResult(self.name, work_data.work_id, {}, {})

        orchestrator = PipelineOrchestrator(seeded_db, LitScopeSettings())
        orchestrator.run_all_works(force=True)
        assert "test-work" in orchestrator._all_timings
        assert len(orchestrator._all_timings["test-work"]) == 1

    def test_failed_analyzer_not_timed(self, seeded_db: Database) -> None:
        class FailAnalyzer(BaseAnalyzer):
            name: ClassVar[str] = "fail_timing"

            def analyze(
                self, work_data: WorkData, context: AnalysisContext
            ) -> AnalysisResult:
                msg = "boom"
                raise RuntimeError(msg)

        orchestrator = PipelineOrchestrator(seeded_db, LitScopeSettings())
        orchestrator.run("test-work", force=True)
        assert len(orchestrator._last_timings) == 0

    def test_multiple_analyzers_timed(self, seeded_db: Database) -> None:
        class Alpha(BaseAnalyzer):
            name: ClassVar[str] = "alpha"

            def analyze(
                self, work_data: WorkData, context: AnalysisContext
            ) -> AnalysisResult:
                return AnalysisResult(self.name, work_data.work_id, {}, {})

        class Beta(BaseAnalyzer):
            name: ClassVar[str] = "beta"
            dependencies: ClassVar[tuple[str, ...]] = ("alpha",)

            def analyze(
                self, work_data: WorkData, context: AnalysisContext
            ) -> AnalysisResult:
                return AnalysisResult(self.name, work_data.work_id, {}, {})

        orchestrator = PipelineOrchestrator(seeded_db, LitScopeSettings())
        orchestrator.run("test-work", force=True)
        assert len(orchestrator._last_timings) == 2
        assert orchestrator._last_timings[0].analyzer_name == "alpha"
        assert orchestrator._last_timings[1].analyzer_name == "beta"


# --- Phase B: Skip already-analyzed ---


class TestSkipAnalyzed:
    def test_skip_when_already_analyzed(self, seeded_db: Database) -> None:
        class SkipMe(BaseAnalyzer):
            name: ClassVar[str] = "skip_me"
            call_count: ClassVar[int] = 0

            def analyze(
                self, work_data: WorkData, context: AnalysisContext
            ) -> AnalysisResult:
                SkipMe.call_count += 1
                return AnalysisResult(self.name, work_data.work_id, {"x": 1.0}, {})

        orchestrator = PipelineOrchestrator(seeded_db, LitScopeSettings())

        # First run — analyze is called
        SkipMe.call_count = 0
        results1 = orchestrator.run("test-work", force=True)
        assert SkipMe.call_count == 1
        assert len(results1) == 1

        # Second run — should skip (analyze not called)
        SkipMe.call_count = 0
        results2 = orchestrator.run("test-work")
        assert SkipMe.call_count == 0
        assert len(results2) == 1
        assert results2[0].analyzer_name == "skip_me"
        assert results2[0].metrics["x"] == 1.0

    def test_force_reruns(self, seeded_db: Database) -> None:
        class ForceMe(BaseAnalyzer):
            name: ClassVar[str] = "force_me"
            call_count: ClassVar[int] = 0

            def analyze(
                self, work_data: WorkData, context: AnalysisContext
            ) -> AnalysisResult:
                ForceMe.call_count += 1
                return AnalysisResult(self.name, work_data.work_id, {}, {})

        orchestrator = PipelineOrchestrator(seeded_db, LitScopeSettings())

        ForceMe.call_count = 0
        orchestrator.run("test-work", force=True)
        assert ForceMe.call_count == 1

        ForceMe.call_count = 0
        orchestrator.run("test-work", force=True)
        assert ForceMe.call_count == 1

    def test_skipped_result_in_context_for_dependents(
        self, seeded_db: Database
    ) -> None:
        class Parent(BaseAnalyzer):
            name: ClassVar[str] = "parent_skip"

            def analyze(
                self, work_data: WorkData, context: AnalysisContext
            ) -> AnalysisResult:
                return AnalysisResult(self.name, work_data.work_id, {"p": 1.0}, {})

        class Child(BaseAnalyzer):
            name: ClassVar[str] = "child_skip"
            dependencies: ClassVar[tuple[str, ...]] = ("parent_skip",)

            def analyze(
                self, work_data: WorkData, context: AnalysisContext
            ) -> AnalysisResult:
                parent = context.get("parent_skip")
                return AnalysisResult(
                    self.name, work_data.work_id, {"got_p": parent.metrics["p"]}, {}
                )

        orchestrator = PipelineOrchestrator(seeded_db, LitScopeSettings())
        # Run parent first to store result
        orchestrator.run("test-work", names=["parent_skip"], force=True)
        # Now run both — parent should be skipped, child should still get context
        results = orchestrator.run("test-work")
        child_result = next(r for r in results if r.analyzer_name == "child_skip")
        assert child_result.metrics["got_p"] == 1.0

    def test_is_analyzed(self, seeded_db: Database) -> None:
        class CheckMe(BaseAnalyzer):
            name: ClassVar[str] = "check_me"

            def analyze(
                self, work_data: WorkData, context: AnalysisContext
            ) -> AnalysisResult:
                return AnalysisResult(self.name, work_data.work_id, {}, {})

        analyzer = CheckMe(seeded_db, LitScopeSettings())
        assert not analyzer.is_analyzed("test-work")

        orchestrator = PipelineOrchestrator(seeded_db, LitScopeSettings())
        orchestrator.run("test-work", force=True)

        assert analyzer.is_analyzed("test-work")

    def test_load_result(self, seeded_db: Database) -> None:
        class LoadMe(BaseAnalyzer):
            name: ClassVar[str] = "load_me"

            def analyze(
                self, work_data: WorkData, context: AnalysisContext
            ) -> AnalysisResult:
                return AnalysisResult(
                    self.name, work_data.work_id, {"a": 2.0}, {"key": "val"}
                )

        orchestrator = PipelineOrchestrator(seeded_db, LitScopeSettings())
        orchestrator.run("test-work", force=True)

        analyzer = LoadMe(seeded_db, LitScopeSettings())
        loaded = analyzer.load_result("test-work")
        assert loaded.analyzer_name == "load_me"
        assert loaded.work_id == "test-work"
        assert loaded.metrics["a"] == 2.0
        assert loaded.data["key"] == "val"


# --- Phase D: Parallel execution ---


class TestBuildLayers:
    def test_single_layer_no_deps(self) -> None:
        class A(BaseAnalyzer):
            name: ClassVar[str] = "a_layer"

            def analyze(self, w: WorkData, c: AnalysisContext) -> AnalysisResult:
                return AnalysisResult(self.name, w.work_id, {}, {})

        class B(BaseAnalyzer):
            name: ClassVar[str] = "b_layer"

            def analyze(self, w: WorkData, c: AnalysisContext) -> AnalysisResult:
                return AnalysisResult(self.name, w.work_id, {}, {})

        layers = _build_layers(["a_layer", "b_layer"])
        assert len(layers) == 1
        assert set(layers[0]) == {"a_layer", "b_layer"}

    def test_two_layers_with_deps(self) -> None:
        class X(BaseAnalyzer):
            name: ClassVar[str] = "x_layer"

            def analyze(self, w: WorkData, c: AnalysisContext) -> AnalysisResult:
                return AnalysisResult(self.name, w.work_id, {}, {})

        class Y(BaseAnalyzer):
            name: ClassVar[str] = "y_layer"
            dependencies: ClassVar[tuple[str, ...]] = ("x_layer",)

            def analyze(self, w: WorkData, c: AnalysisContext) -> AnalysisResult:
                return AnalysisResult(self.name, w.work_id, {}, {})

        layers = _build_layers(["x_layer", "y_layer"])
        assert len(layers) == 2
        assert layers[0] == ["x_layer"]
        assert layers[1] == ["y_layer"]


class TestParallelExecution:
    def test_parallel_produces_same_results(self, seeded_db: Database) -> None:
        class P1(BaseAnalyzer):
            name: ClassVar[str] = "p1"

            def analyze(
                self, work_data: WorkData, context: AnalysisContext
            ) -> AnalysisResult:
                return AnalysisResult(self.name, work_data.work_id, {"v": 1.0}, {})

        class P2(BaseAnalyzer):
            name: ClassVar[str] = "p2"

            def analyze(
                self, work_data: WorkData, context: AnalysisContext
            ) -> AnalysisResult:
                return AnalysisResult(self.name, work_data.work_id, {"v": 2.0}, {})

        class P3(BaseAnalyzer):
            name: ClassVar[str] = "p3"
            dependencies: ClassVar[tuple[str, ...]] = ("p1",)

            def analyze(
                self, work_data: WorkData, context: AnalysisContext
            ) -> AnalysisResult:
                p1_val = context.get("p1").metrics["v"]
                return AnalysisResult(
                    self.name, work_data.work_id, {"v": p1_val + 10}, {}
                )

        orchestrator = PipelineOrchestrator(seeded_db, LitScopeSettings())

        seq_results = orchestrator.run("test-work", force=True)
        seq_metrics = {r.analyzer_name: r.metrics for r in seq_results}

        par_results = orchestrator.run("test-work", force=True, parallel=True)
        par_metrics = {r.analyzer_name: r.metrics for r in par_results}

        assert seq_metrics == par_metrics

    def test_parallel_with_skip(self, seeded_db: Database) -> None:
        class PS1(BaseAnalyzer):
            name: ClassVar[str] = "ps1"
            call_count: ClassVar[int] = 0

            def analyze(
                self, work_data: WorkData, context: AnalysisContext
            ) -> AnalysisResult:
                PS1.call_count += 1
                return AnalysisResult(self.name, work_data.work_id, {"v": 1.0}, {})

        class PS2(BaseAnalyzer):
            name: ClassVar[str] = "ps2"
            call_count: ClassVar[int] = 0

            def analyze(
                self, work_data: WorkData, context: AnalysisContext
            ) -> AnalysisResult:
                PS2.call_count += 1
                return AnalysisResult(self.name, work_data.work_id, {"v": 2.0}, {})

        orchestrator = PipelineOrchestrator(seeded_db, LitScopeSettings())

        PS1.call_count = 0
        PS2.call_count = 0
        orchestrator.run("test-work", force=True, parallel=True)
        assert PS1.call_count == 1
        assert PS2.call_count == 1

        PS1.call_count = 0
        PS2.call_count = 0
        results = orchestrator.run("test-work", parallel=True)
        assert PS1.call_count == 0
        assert PS2.call_count == 0
        assert len(results) == 2


# --- Benchmark ---


class TestPipelineBenchmark:
    def test_run_returns_result(self, seeded_db: Database) -> None:
        class BenchAnalyzer(BaseAnalyzer):
            name: ClassVar[str] = "bench"

            def analyze(
                self, work_data: WorkData, context: AnalysisContext
            ) -> AnalysisResult:
                return AnalysisResult(self.name, work_data.work_id, {"v": 1.0}, {})

        orchestrator = PipelineOrchestrator(seeded_db, LitScopeSettings())
        bm = PipelineBenchmark(orchestrator)
        result = bm.run(["test-work"])

        assert result.work_count == 1
        assert result.analyzer_count == 1
        assert result.total_seconds > 0
        assert result.peak_memory_mb >= 0
        assert result.data_load_seconds >= 0
        assert len(result.analyzer_summaries) == 1
        assert result.analyzer_summaries[0].analyzer_name == "bench"
        assert len(result.work_summaries) == 1
        assert result.work_summaries[0].work_id == "test-work"
        assert result.work_summaries[0].token_count == 20

    def test_run_multiple_works_aggregates_analyzer(self, seeded_db: Database) -> None:
        """Cover the branch where an analyzer name is already in by_analyzer."""
        # Insert a second work so we can benchmark across two works
        seeded_db.conn.execute(
            "INSERT INTO works (work_id, title, author, file_path, file_hash, "
            "pub_year, language, word_count, sent_count, chap_count) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [
                "test-work-2",
                "Second Title",
                "Test Author",
                "/path/to/test2.epub",
                "def456hash",
                1925,
                "en",
                10,
                1,
                1,
            ],
        )
        seeded_db.conn.execute(
            "INSERT INTO chapters (chapter_id, work_id, position, title, "
            "word_count, sent_count) VALUES (?, ?, ?, ?, ?, ?)",
            ["test-work-2::ch000", "test-work-2", 0, "Chapter 1", 10, 1],
        )
        seeded_db.conn.execute(
            "INSERT INTO sentences (sentence_id, work_id, chapter_id, position, "
            "text, word_count, char_count) VALUES (?, ?, ?, ?, ?, ?, ?)",
            [
                "test-work-2::ch000::s000",
                "test-work-2",
                "test-work-2::ch000",
                0,
                "A simple test sentence here.",
                5,
                28,
            ],
        )
        seeded_db.conn.executemany(
            "INSERT INTO tokens (work_id, sentence_id, position, "
            "token, lemma, pos, is_stop) VALUES (?, ?, ?, ?, ?, ?, ?)",
            [
                ("test-work-2", "test-work-2::ch000::s000", 0, "A", "a", "DET", True),
                (
                    "test-work-2",
                    "test-work-2::ch000::s000",
                    1,
                    "simple",
                    "simple",
                    "ADJ",
                    False,
                ),
                (
                    "test-work-2",
                    "test-work-2::ch000::s000",
                    2,
                    "test",
                    "test",
                    "NOUN",
                    False,
                ),
                (
                    "test-work-2",
                    "test-work-2::ch000::s000",
                    3,
                    "sentence",
                    "sentence",
                    "NOUN",
                    False,
                ),
                (
                    "test-work-2",
                    "test-work-2::ch000::s000",
                    4,
                    "here",
                    "here",
                    "ADV",
                    False,
                ),
                (
                    "test-work-2",
                    "test-work-2::ch000::s000",
                    5,
                    ".",
                    ".",
                    "PUNCT",
                    False,
                ),
            ],
        )

        class MultiWorkAnalyzer(BaseAnalyzer):
            name: ClassVar[str] = "multi_work"

            def analyze(
                self, work_data: WorkData, context: AnalysisContext
            ) -> AnalysisResult:
                return AnalysisResult(self.name, work_data.work_id, {"v": 1.0}, {})

        orchestrator = PipelineOrchestrator(seeded_db, LitScopeSettings())
        bm = PipelineBenchmark(orchestrator)
        result = bm.run(["test-work", "test-work-2"])

        assert result.work_count == 2
        assert result.analyzer_count == 1
        assert len(result.analyzer_summaries) == 1
        assert result.analyzer_summaries[0].analyzer_name == "multi_work"
        assert len(result.work_summaries) == 2


class TestFormatters:
    @pytest.fixture
    def sample_result(self) -> BenchmarkResult:
        return BenchmarkResult(
            work_count=1,
            analyzer_count=2,
            total_seconds=5.0,
            peak_memory_mb=128.0,
            data_load_seconds=0.5,
            analyzer_summaries=[
                AnalyzerSummary("vocab", 1.0, 0.2, 1.2, 60.0),
                AnalyzerSummary("pos", 0.5, 0.3, 0.8, 40.0),
            ],
            work_summaries=[
                WorkSummary("test-work", 2.0, 1000, 500.0),
            ],
            timings=[
                AnalyzerTiming("vocab", "test-work", 1.0, 0.2, 1.2),
                AnalyzerTiming("pos", "test-work", 0.5, 0.3, 0.8),
            ],
        )

    def test_format_table(self, sample_result: BenchmarkResult) -> None:
        output = format_table(sample_result)
        assert "=== LitScope Pipeline Benchmark ===" in output
        assert "Works: 1" in output
        assert "Analyzers: 2" in output
        assert "vocab" in output
        assert "pos" in output
        assert "test-work" in output
        assert "Peak 128 MB" in output

    def test_format_csv(self, sample_result: BenchmarkResult) -> None:
        output = format_csv(sample_result)
        lines = [line.strip() for line in output.strip().splitlines()]
        expected_header = (
            "analyzer_name,work_id,analyze_seconds,store_seconds,total_seconds"
        )
        assert lines[0] == expected_header
        assert len(lines) == 3  # header + 2 data rows
        assert "vocab" in lines[1]
        assert "pos" in lines[2]

    def test_format_json(self, sample_result: BenchmarkResult) -> None:
        output = format_json(sample_result)
        data = json.loads(output)
        assert data["work_count"] == 1
        assert data["analyzer_count"] == 2
        assert data["total_seconds"] == 5.0
        assert data["peak_memory_mb"] == 128.0
        assert len(data["analyzer_summaries"]) == 2
        assert len(data["work_summaries"]) == 1
        assert len(data["timings"]) == 2
