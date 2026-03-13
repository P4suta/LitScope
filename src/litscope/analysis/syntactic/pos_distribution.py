"""POS distribution analyzer."""

from __future__ import annotations

from collections import Counter
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
        tokens = work_data.tokens
        total = len(tokens)
        counts: Counter[str] = Counter(t.pos for t in tokens)

        distribution = {
            pos: {"count": count, "ratio": count / total if total > 0 else 0.0}
            for pos, count in counts.most_common()
        }

        return AnalysisResult(
            self.name,
            work_data.work_id,
            {"total_tokens": float(total), "unique_pos": float(len(counts))},
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
