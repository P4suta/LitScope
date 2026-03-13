"""Tests for BaseAnalyzer abstract class."""

import json
from abc import abstractmethod
from typing import ClassVar

import pytest

from litscope.analysis.base import BaseAnalyzer
from litscope.analysis.models import AnalysisContext, AnalysisResult, WorkData
from litscope.config import LitScopeSettings
from litscope.storage.database import Database


class TestBaseAnalyzer:
    def test_abc_not_instantiable(self, seeded_db: Database) -> None:
        with pytest.raises(TypeError):
            BaseAnalyzer(seeded_db, LitScopeSettings())  # type: ignore[abstract]

    def test_concrete_subclass(self, seeded_db: Database) -> None:
        class DummyAnalyzer(BaseAnalyzer):
            name: ClassVar[str] = "_test_dummy_base"
            dependencies: ClassVar[tuple[str, ...]] = ()

            def analyze(
                self, work_data: WorkData, context: AnalysisContext
            ) -> AnalysisResult:
                return AnalysisResult(self.name, work_data.work_id, {}, {})

        analyzer = DummyAnalyzer(seeded_db, LitScopeSettings())
        result = analyzer.analyze(WorkData("test-work", seeded_db), AnalysisContext())
        assert result.analyzer_name == "_test_dummy_base"

    def test_store_result(self, seeded_db: Database) -> None:
        class StoreDummy(BaseAnalyzer):
            name: ClassVar[str] = "_test_store_dummy"

            def analyze(
                self, work_data: WorkData, context: AnalysisContext
            ) -> AnalysisResult:
                return AnalysisResult(self.name, work_data.work_id, {"x": 1.0}, {})

        analyzer = StoreDummy(seeded_db, LitScopeSettings())
        result = AnalysisResult(
            "_test_store_dummy", "test-work", {"x": 1.0}, {"k": "v"}
        )
        analyzer.store_result(result)

        row = seeded_db.conn.execute(
            "SELECT analyzer_name, work_id, metrics, data FROM analysis_results "
            "WHERE analyzer_name = ?",
            ["_test_store_dummy"],
        ).fetchone()
        assert row is not None
        assert row[0] == "_test_store_dummy"
        assert row[1] == "test-work"
        assert json.loads(row[2]) == {"x": 1.0}
        assert json.loads(row[3]) == {"k": "v"}

    def test_store_result_upsert(self, seeded_db: Database) -> None:
        class UpsertDummy(BaseAnalyzer):
            name: ClassVar[str] = "_test_upsert_dummy"

            def analyze(
                self, work_data: WorkData, context: AnalysisContext
            ) -> AnalysisResult:
                return AnalysisResult(self.name, work_data.work_id, {}, {})

        analyzer = UpsertDummy(seeded_db, LitScopeSettings())
        analyzer.store_result(
            AnalysisResult("_test_upsert_dummy", "test-work", {"v": 1.0}, {})
        )
        analyzer.store_result(
            AnalysisResult("_test_upsert_dummy", "test-work", {"v": 2.0}, {})
        )

        row = seeded_db.conn.execute(
            "SELECT metrics FROM analysis_results WHERE analyzer_name = ?",
            ["_test_upsert_dummy"],
        ).fetchone()
        assert row is not None
        assert json.loads(row[0]) == {"v": 2.0}

    def test_abstract_subclass_not_registered(self) -> None:
        """Abstract intermediate subclass should not be registered."""
        from litscope.analysis.registry import AnalyzerRegistry

        before = set(AnalyzerRegistry.all_names())

        class AbstractMiddle(BaseAnalyzer):
            """An abstract subclass with no concrete analyze()."""

            @abstractmethod
            def extra(self) -> None: ...

        assert set(AnalyzerRegistry.all_names()) == before

    def test_subclass_without_name_not_registered(self) -> None:
        """Concrete subclass without `name` attribute should not be registered."""
        from litscope.analysis.registry import AnalyzerRegistry

        before = set(AnalyzerRegistry.all_names())

        class NoNameAnalyzer(BaseAnalyzer):
            def analyze(
                self, work_data: WorkData, context: AnalysisContext
            ) -> AnalysisResult:
                return AnalysisResult("x", work_data.work_id, {}, {})

        assert set(AnalyzerRegistry.all_names()) == before

    def test_dependencies_default_empty(self) -> None:
        assert BaseAnalyzer.dependencies == ()
