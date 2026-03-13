"""Analyzer registry with topological sort for dependency resolution."""

from __future__ import annotations

from typing import TYPE_CHECKING

from litscope.exceptions import AnalyzerNotFoundError, CircularDependencyError

if TYPE_CHECKING:
    from litscope.analysis.base import BaseAnalyzer


class AnalyzerRegistry:
    """Central registry for all analyzer classes."""

    _analyzers: dict[str, type[BaseAnalyzer]] = {}

    @classmethod
    def register(cls, analyzer_cls: type[BaseAnalyzer]) -> None:
        """Register an analyzer class by its name."""
        cls._analyzers[analyzer_cls.name] = analyzer_cls

    @classmethod
    def get(cls, name: str) -> type[BaseAnalyzer]:
        """Get an analyzer class by name, raising if not found."""
        try:
            return cls._analyzers[name]
        except KeyError:
            raise AnalyzerNotFoundError(f"Analyzer not found: {name}") from None

    @classmethod
    def all_names(cls) -> list[str]:
        """Return sorted list of all registered analyzer names."""
        return sorted(cls._analyzers)

    @classmethod
    def resolve_order(cls, names: list[str] | None = None) -> list[str]:
        """Resolve execution order via topological sort (Kahn's algorithm)."""
        targets = set(names) if names else set(cls._analyzers)
        # Collect all needed analyzers including transitive dependencies
        needed: set[str] = set()
        stack = list(targets)
        while stack:
            name = stack.pop()
            if name in needed:
                continue
            needed.add(name)
            analyzer_cls = cls.get(name)
            for dep in analyzer_cls.dependencies:
                if dep not in needed:
                    stack.append(dep)

        # Build adjacency and in-degree
        in_degree: dict[str, int] = {n: 0 for n in needed}
        dependents: dict[str, list[str]] = {n: [] for n in needed}
        for name in needed:
            for dep in cls.get(name).dependencies:
                dependents[dep].append(name)
                in_degree[name] += 1

        # Kahn's algorithm
        queue = sorted(n for n in needed if in_degree[n] == 0)
        order: list[str] = []
        while queue:
            node = queue.pop(0)
            order.append(node)
            for dep in sorted(dependents[node]):
                in_degree[dep] -= 1
                if in_degree[dep] == 0:
                    queue.append(dep)

        if len(order) != len(needed):
            msg = "Circular dependency detected among analyzers"
            raise CircularDependencyError(msg)
        return order

    @classmethod
    def discover(cls) -> None:
        """Import all analyzer subpackages to trigger registration."""
        import importlib
        import pkgutil

        import litscope.analysis as pkg

        for _importer, modname, ispkg in pkgutil.walk_packages(
            pkg.__path__, prefix=pkg.__name__ + "."
        ):
            if modname != "litscope.analysis.registry":
                importlib.import_module(modname)

    @classmethod
    def clear(cls) -> None:
        """Clear all registered analyzers (for testing)."""
        cls._analyzers.clear()
