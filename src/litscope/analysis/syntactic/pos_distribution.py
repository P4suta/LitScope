"""POS distribution analyzer."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from litscope.analysis.base import BaseAnalyzer
from litscope.analysis.models import AnalysisResult

if TYPE_CHECKING:
    from litscope.analysis.models import AnalysisContext, WorkData


class PosDistributionAnalyzer(BaseAnalyzer):
    """Count POS tag frequencies and compute ratios."""

    name: ClassVar[str] = "pos_distribution"
    dependencies: ClassVar[tuple[str, ...]] = ()

    def analyze(self, work_data: WorkData, context: AnalysisContext) -> AnalysisResult:
        """Count POS tags from all tokens."""
        pos_counts = work_data.pos_counts
        total = sum(count for _, count in pos_counts)

        distribution = {
            pos: {"count": count, "ratio": count / total if total > 0 else 0.0}
            for pos, count in pos_counts
        }

        return AnalysisResult(
            self.name,
            work_data.work_id,
            {"total_tokens": float(total), "unique_pos": float(len(pos_counts))},
            {"distribution": distribution},
        )

    def store_result(self, result: AnalysisResult) -> None:
        """Store POS distribution in pos_distributions table."""
        super().store_result(result)
        conn = self._db.conn
        conn.execute(
            "DELETE FROM pos_distributions WHERE work_id = ?", [result.work_id]
        )
        distribution: dict[str, dict[str, float]] = result.data.get("distribution", {})
        if distribution:
            conn.executemany(
                "INSERT INTO pos_distributions (work_id, pos, count, ratio) "
                "VALUES (?, ?, ?, ?)",
                [
                    (result.work_id, pos, int(info["count"]), info["ratio"])
                    for pos, info in distribution.items()
                ],
            )
