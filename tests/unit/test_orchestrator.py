"""Tests for PipelineOrchestrator."""

from typing import ClassVar

import pytest

from litscope.analysis.base import BaseAnalyzer
from litscope.analysis.models import AnalysisContext, AnalysisResult, WorkData
from litscope.analysis.orchestrator import PipelineOrchestrator
from litscope.analysis.registry import AnalyzerRegistry
from litscope.config import LitScopeSettings
from litscope.storage.database import Database


@pytest.fixture(autouse=True)
def _clean_registry() -> None:  # type: ignore[misc]
    saved = dict(AnalyzerRegistry._analyzers)
    AnalyzerRegistry.clear()
    yield  # type: ignore[misc]
    AnalyzerRegistry._analyzers.clear()
    AnalyzerRegistry._analyzers.update(saved)


class TestPipelineOrchestrator:
    def test_run_single_analyzer(self, seeded_db: Database) -> None:
        class SimpleAnalyzer(BaseAnalyzer):
            name: ClassVar[str] = "simple"

            def analyze(
                self, work_data: WorkData, context: AnalysisContext
            ) -> AnalysisResult:
                return AnalysisResult(self.name, work_data.work_id, {"count": 1.0}, {})

        orchestrator = PipelineOrchestrator(seeded_db, LitScopeSettings())
        results = orchestrator.run("test-work")
        assert len(results) == 1
        assert results[0].analyzer_name == "simple"

    def test_dependency_order(self, seeded_db: Database) -> None:
        execution_order: list[str] = []

        class First(BaseAnalyzer):
            name: ClassVar[str] = "first"

            def analyze(
                self, work_data: WorkData, context: AnalysisContext
            ) -> AnalysisResult:
                execution_order.append("first")
                return AnalysisResult(self.name, work_data.work_id, {}, {})

        class Second(BaseAnalyzer):
            name: ClassVar[str] = "second"
            dependencies: ClassVar[tuple[str, ...]] = ("first",)

            def analyze(
                self, work_data: WorkData, context: AnalysisContext
            ) -> AnalysisResult:
                execution_order.append("second")
                assert context.has("first")
                return AnalysisResult(self.name, work_data.work_id, {}, {})

        orchestrator = PipelineOrchestrator(seeded_db, LitScopeSettings())
        results = orchestrator.run("test-work")
        assert execution_order == ["first", "second"]
        assert len(results) == 2

    def test_error_isolation(self, seeded_db: Database) -> None:
        class GoodAnalyzer(BaseAnalyzer):
            name: ClassVar[str] = "good"

            def analyze(
                self, work_data: WorkData, context: AnalysisContext
            ) -> AnalysisResult:
                return AnalysisResult(self.name, work_data.work_id, {}, {})

        class BadAnalyzer(BaseAnalyzer):
            name: ClassVar[str] = "bad"

            def analyze(
                self, work_data: WorkData, context: AnalysisContext
            ) -> AnalysisResult:
                msg = "boom"
                raise RuntimeError(msg)

        orchestrator = PipelineOrchestrator(seeded_db, LitScopeSettings())
        results = orchestrator.run("test-work")
        assert len(results) == 1
        assert results[0].analyzer_name == "good"

    def test_skip_dependents_of_failed(self, seeded_db: Database) -> None:
        class FailAnalyzer(BaseAnalyzer):
            name: ClassVar[str] = "fail_parent"

            def analyze(
                self, work_data: WorkData, context: AnalysisContext
            ) -> AnalysisResult:
                msg = "fail"
                raise RuntimeError(msg)

        class ChildAnalyzer(BaseAnalyzer):
            name: ClassVar[str] = "child"
            dependencies: ClassVar[tuple[str, ...]] = ("fail_parent",)

            def analyze(
                self, work_data: WorkData, context: AnalysisContext
            ) -> AnalysisResult:
                return AnalysisResult(self.name, work_data.work_id, {}, {})

        orchestrator = PipelineOrchestrator(seeded_db, LitScopeSettings())
        results = orchestrator.run("test-work")
        assert len(results) == 0

    def test_run_all_works(self, seeded_db: Database) -> None:
        class AllWorksAnalyzer(BaseAnalyzer):
            name: ClassVar[str] = "all_works"

            def analyze(
                self, work_data: WorkData, context: AnalysisContext
            ) -> AnalysisResult:
                return AnalysisResult(self.name, work_data.work_id, {}, {})

        orchestrator = PipelineOrchestrator(seeded_db, LitScopeSettings())
        all_results = orchestrator.run_all_works()
        assert "test-work" in all_results
        assert len(all_results["test-work"]) == 1

    def test_run_subset(self, seeded_db: Database) -> None:
        class A(BaseAnalyzer):
            name: ClassVar[str] = "a_sub"

            def analyze(
                self, work_data: WorkData, context: AnalysisContext
            ) -> AnalysisResult:
                return AnalysisResult(self.name, work_data.work_id, {}, {})

        class B(BaseAnalyzer):
            name: ClassVar[str] = "b_sub"

            def analyze(
                self, work_data: WorkData, context: AnalysisContext
            ) -> AnalysisResult:
                return AnalysisResult(self.name, work_data.work_id, {}, {})

        orchestrator = PipelineOrchestrator(seeded_db, LitScopeSettings())
        results = orchestrator.run("test-work", names=["a_sub"])
        assert len(results) == 1
        assert results[0].analyzer_name == "a_sub"

    def test_skip_already_analyzed(self, seeded_db: Database) -> None:
        """Analyzers with existing results are skipped and loaded from DB."""
        call_count = 0

        class SkipAnalyzer(BaseAnalyzer):
            name: ClassVar[str] = "skippable"

            def analyze(
                self, work_data: WorkData, context: AnalysisContext
            ) -> AnalysisResult:
                nonlocal call_count
                call_count += 1
                return AnalysisResult(self.name, work_data.work_id, {"v": 1.0}, {})

        orchestrator = PipelineOrchestrator(seeded_db, LitScopeSettings())

        # First run — analyze() is called and result stored
        results1 = orchestrator.run("test-work")
        assert len(results1) == 1
        assert call_count == 1

        # Second run — should skip (load from DB, no analyze() call)
        call_count = 0
        results2 = orchestrator.run("test-work")
        assert len(results2) == 1
        assert call_count == 0
        assert results2[0].analyzer_name == "skippable"
        assert results2[0].metrics == {"v": 1.0}

    def test_force_reruns_analyzed(self, seeded_db: Database) -> None:
        """force=True re-runs analyzers even when results exist."""
        call_count = 0

        class ForceAnalyzer(BaseAnalyzer):
            name: ClassVar[str] = "forceable"

            def analyze(
                self, work_data: WorkData, context: AnalysisContext
            ) -> AnalysisResult:
                nonlocal call_count
                call_count += 1
                return AnalysisResult(
                    self.name, work_data.work_id, {"run": float(call_count)}, {}
                )

        orchestrator = PipelineOrchestrator(seeded_db, LitScopeSettings())

        # First run
        orchestrator.run("test-work")
        assert call_count == 1

        # Force re-run — analyze() called again
        results = orchestrator.run("test-work", force=True)
        assert call_count == 2
        assert results[0].metrics["run"] == 2.0

    def test_skip_restores_context_for_dependents(self, seeded_db: Database) -> None:
        """Skipped analyzer's result is available in context for dependents."""
        child_saw_parent = False

        class Parent(BaseAnalyzer):
            name: ClassVar[str] = "skip_parent"

            def analyze(
                self, work_data: WorkData, context: AnalysisContext
            ) -> AnalysisResult:
                return AnalysisResult(
                    self.name, work_data.work_id, {"parent": 1.0}, {"key": "val"}
                )

        class Child(BaseAnalyzer):
            name: ClassVar[str] = "skip_child"
            dependencies: ClassVar[tuple[str, ...]] = ("skip_parent",)

            def analyze(
                self, work_data: WorkData, context: AnalysisContext
            ) -> AnalysisResult:
                nonlocal child_saw_parent
                parent_result = context.get("skip_parent")
                child_saw_parent = parent_result.metrics.get("parent") == 1.0
                return AnalysisResult(self.name, work_data.work_id, {}, {})

        orchestrator = PipelineOrchestrator(seeded_db, LitScopeSettings())

        # First run — both execute
        orchestrator.run("test-work")
        assert child_saw_parent

        # Delete child result so parent is skipped but child re-runs
        seeded_db.conn.execute(
            "DELETE FROM analysis_results WHERE analyzer_name = 'skip_child'"
        )
        child_saw_parent = False
        results = orchestrator.run("test-work", names=["skip_parent", "skip_child"])
        assert child_saw_parent
        assert len(results) == 2

    def test_parallel_basic(self, seeded_db: Database) -> None:
        """Parallel mode runs independent analyzers concurrently."""
        executed: list[str] = []

        class ParA(BaseAnalyzer):
            name: ClassVar[str] = "par_a"

            def analyze(
                self, work_data: WorkData, context: AnalysisContext
            ) -> AnalysisResult:
                executed.append("par_a")
                return AnalysisResult(self.name, work_data.work_id, {}, {})

        class ParB(BaseAnalyzer):
            name: ClassVar[str] = "par_b"

            def analyze(
                self, work_data: WorkData, context: AnalysisContext
            ) -> AnalysisResult:
                executed.append("par_b")
                return AnalysisResult(self.name, work_data.work_id, {}, {})

        orchestrator = PipelineOrchestrator(seeded_db, LitScopeSettings())
        results = orchestrator.run("test-work", parallel=True)
        assert len(results) == 2
        assert set(executed) == {"par_a", "par_b"}

    def test_parallel_skip_already_analyzed(self, seeded_db: Database) -> None:
        """Parallel mode skips already-analyzed and loads from DB."""
        call_count = 0

        class ParSkip(BaseAnalyzer):
            name: ClassVar[str] = "par_skip"

            def analyze(
                self, work_data: WorkData, context: AnalysisContext
            ) -> AnalysisResult:
                nonlocal call_count
                call_count += 1
                return AnalysisResult(self.name, work_data.work_id, {"n": 1.0}, {})

        orchestrator = PipelineOrchestrator(seeded_db, LitScopeSettings())

        # First run
        orchestrator.run("test-work", parallel=True)
        assert call_count == 1

        # Second run — skipped
        call_count = 0
        results = orchestrator.run("test-work", parallel=True)
        assert call_count == 0
        assert len(results) == 1
        assert results[0].metrics == {"n": 1.0}
