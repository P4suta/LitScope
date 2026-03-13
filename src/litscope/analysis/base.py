"""Base analyzer abstract class."""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, ClassVar

import structlog

if TYPE_CHECKING:
    from litscope.analysis.models import AnalysisContext, AnalysisResult, WorkData
    from litscope.config import LitScopeSettings
    from litscope.storage.database import Database

logger = structlog.get_logger()


class BaseAnalyzer(ABC):
    """Abstract base class for all analyzers."""

    name: ClassVar[str]
    dependencies: ClassVar[tuple[str, ...]] = ()

    def __init__(self, db: Database, settings: LitScopeSettings) -> None:
        self._db = db
        self._settings = settings

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if not getattr(cls, "__abstractmethods__", None) and hasattr(cls, "name"):
            from litscope.analysis.registry import AnalyzerRegistry

            AnalyzerRegistry.register(cls)

    @abstractmethod
    def analyze(self, work_data: WorkData, context: AnalysisContext) -> AnalysisResult:
        """Run analysis on a work and return results."""

    def is_analyzed(self, work_id: str) -> bool:
        """Check if results already exist for this analyzer + work_id."""
        row = self._db.conn.execute(
            "SELECT 1 FROM analysis_results WHERE analyzer_name = ? AND work_id = ?",
            [self.name, work_id],
        ).fetchone()
        return row is not None

    def load_result(self, work_id: str) -> AnalysisResult:
        """Load existing analysis result from the database."""
        from litscope.analysis.models import AnalysisResult

        row = self._db.conn.execute(
            "SELECT metrics, data FROM analysis_results "
            "WHERE analyzer_name = ? AND work_id = ?",
            [self.name, work_id],
        ).fetchone()
        if row is None:
            msg = f"No result for {self.name} on {work_id}"
            raise ValueError(msg)
        return AnalysisResult(
            analyzer_name=self.name,
            work_id=work_id,
            metrics=json.loads(row[0]),
            data=json.loads(row[1]),
        )

    def store_result(self, result: AnalysisResult) -> None:
        """Store analysis result in the analysis_results table."""
        self._db.conn.execute(
            "DELETE FROM analysis_results WHERE analyzer_name = ? AND work_id = ?",
            [result.analyzer_name, result.work_id],
        )
        self._db.conn.execute(
            "INSERT INTO analysis_results (id, analyzer_name, work_id, metrics, data) "
            "VALUES (nextval('seq_analysis_results'), ?, ?, ?, ?)",
            [
                result.analyzer_name,
                result.work_id,
                json.dumps(result.metrics),
                json.dumps(result.data),
            ],
        )
