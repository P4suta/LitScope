"""POS transition analyzer."""

from __future__ import annotations

from collections import Counter
from typing import TYPE_CHECKING, ClassVar

from litscope.analysis.base import BaseAnalyzer
from litscope.analysis.models import AnalysisResult

if TYPE_CHECKING:
    from litscope.analysis.models import AnalysisContext, WorkData


class PosTransitionAnalyzer(BaseAnalyzer):
    """Build POS bigram transition matrix within sentences."""

    name: ClassVar[str] = "pos_transition"
    dependencies: ClassVar[tuple[str, ...]] = ("pos_distribution",)

    def analyze(self, work_data: WorkData, context: AnalysisContext) -> AnalysisResult:
        """Compute POS bigram transitions grouped by sentence."""
        tokens = work_data.tokens
        # Group tokens by sentence
        sentence_tokens: dict[str, list[str]] = {}
        for t in tokens:
            sentence_tokens.setdefault(t.sentence_id, []).append(t.pos)

        bigram_counts: Counter[tuple[str, str]] = Counter()
        for pos_list in sentence_tokens.values():
            for i in range(len(pos_list) - 1):
                bigram_counts[(pos_list[i], pos_list[i + 1])] += 1

        total = sum(bigram_counts.values())
        transitions = {
            f"{from_pos}->{to_pos}": {
                "from_pos": from_pos,
                "to_pos": to_pos,
                "count": count,
                "ratio": count / total if total > 0 else 0.0,
            }
            for (from_pos, to_pos), count in bigram_counts.most_common()
        }

        return AnalysisResult(
            self.name,
            work_data.work_id,
            {"total_transitions": float(total), "unique_bigrams": float(len(bigram_counts))},
            {"transitions": transitions},
        )

    def store_result(self, result: AnalysisResult) -> None:
        """Store transitions in pos_transitions table."""
        super().store_result(result)
        conn = self._db.conn
        conn.execute(
            "DELETE FROM pos_transitions WHERE work_id = ?", [result.work_id]
        )
        transitions: dict[str, dict[str, object]] = result.data.get("transitions", {})
        if transitions:
            conn.executemany(
                "INSERT INTO pos_transitions (work_id, from_pos, to_pos, count, ratio) "
                "VALUES (?, ?, ?, ?, ?)",
                [
                    (
                        result.work_id,
                        info["from_pos"],
                        info["to_pos"],
                        int(info["count"]),  # type: ignore[arg-type]
                        info["ratio"],
                    )
                    for info in transitions.values()
                ],
            )
