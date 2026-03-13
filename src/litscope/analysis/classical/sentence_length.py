"""Sentence length analyzer."""

from __future__ import annotations

import statistics
from typing import TYPE_CHECKING, ClassVar

from litscope.analysis.base import BaseAnalyzer
from litscope.analysis.models import AnalysisResult

if TYPE_CHECKING:
    from litscope.analysis.models import AnalysisContext, WorkData


class SentenceLengthAnalyzer(BaseAnalyzer):
    """Compute sentence length statistics."""

    name: ClassVar[str] = "sentence_length"
    dependencies: ClassVar[tuple[str, ...]] = ()

    def analyze(self, work_data: WorkData, context: AnalysisContext) -> AnalysisResult:
        """Compute mean, median, stdev, min, max of sentence word counts."""
        lengths = [
            s.word_count for s in work_data.sentences if s.word_count is not None
        ]

        if not lengths:
            return AnalysisResult(
                self.name,
                work_data.work_id,
                {"mean": 0.0, "median": 0.0, "stdev": 0.0, "min": 0.0, "max": 0.0},
                {},
            )

        stdev = statistics.stdev(lengths) if len(lengths) > 1 else 0.0
        return AnalysisResult(
            self.name,
            work_data.work_id,
            {
                "mean": statistics.mean(lengths),
                "median": float(statistics.median(lengths)),
                "stdev": stdev,
                "min": float(min(lengths)),
                "max": float(max(lengths)),
            },
            {},
        )
