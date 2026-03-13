"""Readability analyzer."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

import syllables

from litscope.analysis.base import BaseAnalyzer
from litscope.analysis.models import AnalysisResult

if TYPE_CHECKING:
    from litscope.analysis.models import AnalysisContext, WorkData


class ReadabilityAnalyzer(BaseAnalyzer):
    """Compute readability scores: Flesch-Kincaid, Coleman-Liau, ARI."""

    name: ClassVar[str] = "readability"
    dependencies: ClassVar[tuple[str, ...]] = ()

    def analyze(self, work_data: WorkData, context: AnalysisContext) -> AnalysisResult:
        """Compute readability indices from sentences and tokens."""
        sentences = work_data.sentences
        tokens = [t for t in work_data.tokens if t.pos != "PUNCT"]

        total_sentences = len(sentences)
        total_words = len(tokens)

        if total_sentences == 0 or total_words == 0:
            return AnalysisResult(
                self.name,
                work_data.work_id,
                {"flesch_kincaid": 0.0, "coleman_liau": 0.0, "ari": 0.0},
                {},
            )

        total_syllables = sum(
            max(syllables.estimate(t.token), 1) for t in tokens
        )
        total_chars = sum(len(t.token) for t in tokens)

        # Flesch-Kincaid Grade Level
        fk = (
            0.39 * (total_words / total_sentences)
            + 11.8 * (total_syllables / total_words)
            - 15.59
        )

        # Coleman-Liau Index
        l = (total_chars / total_words) * 100  # avg chars per 100 words
        s = (total_sentences / total_words) * 100  # avg sentences per 100 words
        cli = 0.0588 * l - 0.296 * s - 15.8

        # Automated Readability Index
        ari = (
            4.71 * (total_chars / total_words)
            + 0.5 * (total_words / total_sentences)
            - 21.43
        )

        return AnalysisResult(
            self.name,
            work_data.work_id,
            {"flesch_kincaid": fk, "coleman_liau": cli, "ari": ari},
            {},
        )
