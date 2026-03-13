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
    AnalyzerRegistry.clear()
    yield  # type: ignore[misc]
    AnalyzerRegistry.clear()


class TestPipelineOrchestrator:
    def test_run_single_analyzer(self, seeded_db: Database) -> None:
        class SimpleAnalyzer(BaseAnalyzer):
            name: ClassVar[str] = "simple"

            def analyze(
                self, work_data: WorkData, context: AnalysisContext
            ) -> AnalysisResult:
                return AnalysisResult(
                    self.name, work_data.work_id, {"count": 1.0}, {}
                )

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
