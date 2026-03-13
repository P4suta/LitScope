"""Vocabulary frequency analyzer."""

from __future__ import annotations

from collections import Counter
from typing import TYPE_CHECKING, Any, ClassVar

from litscope.analysis.base import BaseAnalyzer
from litscope.analysis.models import AnalysisResult

if TYPE_CHECKING:
    from litscope.analysis.models import AnalysisContext, WorkData


class VocabularyFrequencyAnalyzer(BaseAnalyzer):
    """Count lemma frequencies and compute term frequency (TF)."""

    name: ClassVar[str] = "vocabulary_frequency"
    dependencies: ClassVar[tuple[str, ...]] = ()

    def analyze(self, work_data: WorkData, context: AnalysisContext) -> AnalysisResult:
        """Count lemma frequencies from tokens, excluding punctuation."""
        tokens = work_data.tokens
        content_tokens = [t for t in tokens if t.pos != "PUNCT"]
        total = len(content_tokens)
        counts: Counter[str] = Counter(t.lemma.lower() for t in content_tokens)
        frequencies: dict[str, Any] = (
            {
                lemma: {"count": count, "tf": count / total}
                for lemma, count in counts.most_common()
            }
            if total > 0
            else {}
        )

        return AnalysisResult(
            analyzer_name=self.name,
            work_id=work_data.work_id,
            metrics={
                "total_types": float(len(counts)),
                "total_tokens": float(total),
            },
            data={"frequencies": frequencies},
        )

    def store_result(self, result: AnalysisResult) -> None:
        """Store frequencies in word_frequencies and analysis_results."""
        super().store_result(result)
        conn = self._db.conn
        conn.execute("DELETE FROM word_frequencies WHERE work_id = ?", [result.work_id])
        frequencies: dict[str, Any] = result.data.get("frequencies", {})
        if frequencies:
            conn.executemany(
                "INSERT INTO word_frequencies (work_id, lemma, count, tf) "
                "VALUES (?, ?, ?, ?)",
                [
                    (result.work_id, lemma, info["count"], info["tf"])
                    for lemma, info in frequencies.items()
                ],
            )
