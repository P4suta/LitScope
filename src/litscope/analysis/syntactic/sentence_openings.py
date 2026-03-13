"""Sentence openings analyzer."""

from __future__ import annotations

from collections import Counter
from typing import TYPE_CHECKING, ClassVar

from litscope.analysis.base import BaseAnalyzer
from litscope.analysis.models import AnalysisResult

if TYPE_CHECKING:
    from litscope.analysis.models import AnalysisContext, WorkData


class SentenceOpeningsAnalyzer(BaseAnalyzer):
    """Analyze the POS patterns at the start of sentences."""

    name: ClassVar[str] = "sentence_openings"
    dependencies: ClassVar[tuple[str, ...]] = ("pos_distribution",)

    def analyze(self, work_data: WorkData, context: AnalysisContext) -> AnalysisResult:
        """Extract first 1-3 POS tags (skipping PUNCT) per sentence."""
        tokens = work_data.tokens
        # Group tokens by sentence
        sentence_tokens: dict[str, list[str]] = {}
        for t in tokens:
            sentence_tokens.setdefault(t.sentence_id, []).append(t.pos)

        patterns: Counter[str] = Counter()
        total = 0
        for pos_list in sentence_tokens.values():
            # Skip leading PUNCT
            non_punct = [p for p in pos_list if p != "PUNCT"]
            if not non_punct:
                continue
            total += 1
            for n in range(1, min(4, len(non_punct) + 1)):
                pattern = " ".join(non_punct[:n])
                patterns[pattern] += 1

        result_data = {
            pattern: {"count": count, "ratio": count / total if total > 0 else 0.0}
            for pattern, count in patterns.most_common()
        }

        return AnalysisResult(
            self.name,
            work_data.work_id,
            {"total_sentences": float(total), "unique_patterns": float(len(patterns))},
            {"patterns": result_data},
        )

    def store_result(self, result: AnalysisResult) -> None:
        """Store opening patterns in sentence_opening_patterns table."""
        super().store_result(result)
        conn = self._db.conn
        conn.execute(
            "DELETE FROM sentence_opening_patterns WHERE work_id = ?",
            [result.work_id],
        )
        patterns: dict[str, dict[str, float]] = result.data.get("patterns", {})
        if patterns:
            conn.executemany(
                "INSERT INTO sentence_opening_patterns "
                "(work_id, pattern, count, ratio) VALUES (?, ?, ?, ?)",
                [
                    (result.work_id, pattern, int(info["count"]), info["ratio"])
                    for pattern, info in patterns.items()
                ],
            )
