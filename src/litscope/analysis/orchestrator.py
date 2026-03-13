"""Pipeline orchestrator for running analyzers in dependency order."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from litscope.analysis.models import AnalysisContext, WorkData
from litscope.analysis.registry import AnalyzerRegistry

if TYPE_CHECKING:
    from litscope.analysis.models import AnalysisResult
    from litscope.config import LitScopeSettings
    from litscope.storage.database import Database

logger = structlog.get_logger()


class PipelineOrchestrator:
    """Orchestrates analyzer execution in dependency order."""

    def __init__(self, db: Database, settings: LitScopeSettings) -> None:
        self._db = db
        self._settings = settings

    def run(
        self, work_id: str, names: list[str] | None = None
    ) -> list[AnalysisResult]:
        """Run analyzers for a single work in dependency order."""
        order = AnalyzerRegistry.resolve_order(names)
        work_data = WorkData(work_id=work_id, _db=self._db)
        context = AnalysisContext()
        results: list[AnalysisResult] = []
        failed: set[str] = set()

        for analyzer_name in order:
            analyzer_cls = AnalyzerRegistry.get(analyzer_name)
            # Skip if any dependency failed
            if any(dep in failed for dep in analyzer_cls.dependencies):
                logger.warning(
                    "skipping_analyzer",
                    analyzer=analyzer_name,
                    reason="dependency_failed",
                )
                failed.add(analyzer_name)
                continue

            try:
                analyzer = analyzer_cls(self._db, self._settings)
                result = analyzer.analyze(work_data, context)
                analyzer.store_result(result)
                context.set(analyzer_name, result)
                results.append(result)
                logger.info("analyzer_completed", analyzer=analyzer_name, work_id=work_id)
            except Exception:
                logger.exception(
                    "analyzer_failed", analyzer=analyzer_name, work_id=work_id
                )
                failed.add(analyzer_name)

        return results

    def run_all_works(
        self, names: list[str] | None = None
    ) -> dict[str, list[AnalysisResult]]:
        """Run analyzers for all works in the database."""
        rows = self._db.conn.execute("SELECT work_id FROM works").fetchall()
        return {row[0]: self.run(row[0], names) for row in rows}
