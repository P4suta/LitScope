"""Zipf fitness analyzer."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

import numpy as np

from litscope.analysis.base import BaseAnalyzer
from litscope.analysis.models import AnalysisResult

if TYPE_CHECKING:
    from litscope.analysis.models import AnalysisContext, WorkData


class ZipfFitnessAnalyzer(BaseAnalyzer):
    """Measure how well word frequencies fit Zipf's law via log-log regression."""

    name: ClassVar[str] = "zipf_fitness"
    dependencies: ClassVar[tuple[str, ...]] = ("vocabulary_frequency",)

    def analyze(self, work_data: WorkData, context: AnalysisContext) -> AnalysisResult:
        """Compute Zipf's law fitness: alpha, R², intercept."""
        vocab_result = context.get("vocabulary_frequency")
        frequencies: dict[str, dict[str, float]] = vocab_result.data["frequencies"]

        if len(frequencies) < 2:
            return AnalysisResult(
                self.name,
                work_data.work_id,
                {"alpha": 0.0, "r_squared": 0.0, "intercept": 0.0},
                {},
            )

        counts = sorted(
            (int(info["count"]) for info in frequencies.values()), reverse=True
        )
        ranks = np.arange(1, len(counts) + 1, dtype=np.float64)
        log_ranks = np.log(ranks)
        log_counts = np.log(np.array(counts, dtype=np.float64))

        # Linear regression on log-log
        coeffs = np.polyfit(log_ranks, log_counts, 1)
        alpha = float(coeffs[0])
        intercept = float(coeffs[1])

        # R²
        predicted = np.polyval(coeffs, log_ranks)
        ss_res = float(np.sum((log_counts - predicted) ** 2))
        ss_tot = float(np.sum((log_counts - np.mean(log_counts)) ** 2))
        r_squared = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0

        return AnalysisResult(
            self.name,
            work_data.work_id,
            {"alpha": alpha, "r_squared": r_squared, "intercept": intercept},
            {},
        )
