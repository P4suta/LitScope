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
        total_sentences = len(work_data.sentences)
        token_texts = work_data.content_token_texts
        total_words = len(token_texts)

        if total_sentences == 0 or total_words == 0:
            return AnalysisResult(
                self.name,
                work_data.work_id,
                {"flesch_kincaid": 0.0, "coleman_liau": 0.0, "ari": 0.0},
                {},
            )

        total_syllables = sum(max(syllables.estimate(t), 1) for t in token_texts)
        total_chars = work_data.content_char_total

        # Flesch-Kincaid Grade Level
        fk = (
            0.39 * (total_words / total_sentences)
            + 11.8 * (total_syllables / total_words)
            - 15.59
        )

        # Coleman-Liau Index
        chars_per_100 = (total_chars / total_words) * 100
        sents_per_100 = (total_sentences / total_words) * 100
        cli = 0.0588 * chars_per_100 - 0.296 * sents_per_100 - 15.8

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
