"""Tests for AnalyzerRegistry with topological sort."""

from typing import ClassVar

import pytest

from litscope.analysis.base import BaseAnalyzer
from litscope.analysis.models import AnalysisContext, AnalysisResult, WorkData
from litscope.analysis.registry import AnalyzerRegistry
from litscope.exceptions import AnalyzerNotFoundError, CircularDependencyError


@pytest.fixture(autouse=True)
def _clean_registry() -> None:  # type: ignore[misc]
    """Clear registry before each test to avoid cross-contamination."""
    AnalyzerRegistry.clear()
    yield  # type: ignore[misc]
    AnalyzerRegistry.clear()


def _make_analyzer(name: str, deps: tuple[str, ...] = ()) -> type[BaseAnalyzer]:
    """Create a concrete analyzer class with given name and dependencies."""
    cls = type(
        f"_Test{name.title()}Analyzer",
        (BaseAnalyzer,),
        {
            "name": name,
            "dependencies": deps,
            "analyze": lambda self, work_data, context: AnalysisResult(
                self.name, work_data.work_id, {}, {}
            ),
        },
    )
    # ClassVar annotations for mypy
    cls.__annotations__ = {
        "name": ClassVar[str],
        "dependencies": ClassVar[tuple[str, ...]],
    }
    return cls  # type: ignore[return-value]


class TestRegistration:
    def test_register_and_get(self) -> None:
        cls = _make_analyzer("alpha")
        assert AnalyzerRegistry.get("alpha") is cls

    def test_get_not_found(self) -> None:
        with pytest.raises(AnalyzerNotFoundError, match="not found"):
            AnalyzerRegistry.get("nonexistent")

    def test_all_names(self) -> None:
        _make_analyzer("beta")
        _make_analyzer("alpha")
        assert AnalyzerRegistry.all_names() == ["alpha", "beta"]

    def test_clear(self) -> None:
        _make_analyzer("gamma")
        AnalyzerRegistry.clear()
        assert AnalyzerRegistry.all_names() == []

    def test_auto_registration_via_subclass(self) -> None:
        class AutoReg(BaseAnalyzer):
            name: ClassVar[str] = "_test_auto_reg"

            def analyze(
                self, work_data: WorkData, context: AnalysisContext
            ) -> AnalysisResult:
                return AnalysisResult(self.name, work_data.work_id, {}, {})

        assert AnalyzerRegistry.get("_test_auto_reg") is AutoReg


class TestTopologicalSort:
    def test_no_dependencies(self) -> None:
        _make_analyzer("a")
        _make_analyzer("b")
        order = AnalyzerRegistry.resolve_order()
        assert set(order) == {"a", "b"}

    def test_linear_chain(self) -> None:
        _make_analyzer("a")
        _make_analyzer("b", ("a",))
        _make_analyzer("c", ("b",))
        order = AnalyzerRegistry.resolve_order()
        assert order.index("a") < order.index("b") < order.index("c")

    def test_diamond(self) -> None:
        _make_analyzer("a")
        _make_analyzer("b", ("a",))
        _make_analyzer("c", ("a",))
        _make_analyzer("d", ("b", "c"))
        order = AnalyzerRegistry.resolve_order()
        assert order.index("a") < order.index("b")
        assert order.index("a") < order.index("c")
        assert order.index("b") < order.index("d")
        assert order.index("c") < order.index("d")

    def test_subset(self) -> None:
        _make_analyzer("a")
        _make_analyzer("b", ("a",))
        _make_analyzer("c")
        order = AnalyzerRegistry.resolve_order(["b"])
        assert order == ["a", "b"]

    def test_circular_dependency(self) -> None:
        _make_analyzer("x", ("y",))
        _make_analyzer("y", ("x",))
        with pytest.raises(CircularDependencyError):
            AnalyzerRegistry.resolve_order()

    def test_resolve_all(self) -> None:
        _make_analyzer("a")
        _make_analyzer("b", ("a",))
        order = AnalyzerRegistry.resolve_order()
        assert order == ["a", "b"]
