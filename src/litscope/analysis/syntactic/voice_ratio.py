"""Voice ratio analyzer for active/passive voice detection."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

import spacy

from litscope.analysis.base import BaseAnalyzer
from litscope.analysis.models import AnalysisResult

if TYPE_CHECKING:
    from litscope.analysis.models import AnalysisContext, WorkData


class VoiceRatioAnalyzer(BaseAnalyzer):
    """Detect passive voice via dependency parsing."""

    name: ClassVar[str] = "voice_ratio"
    dependencies: ClassVar[tuple[str, ...]] = ("pos_distribution",)

    _nlp: spacy.language.Language | None = None

    def _get_nlp(self) -> spacy.language.Language:
        """Load spaCy model with parser (cached at class level)."""
        if VoiceRatioAnalyzer._nlp is None:
            VoiceRatioAnalyzer._nlp = spacy.load(
                self._settings.spacy_model,
                disable=["ner"],
            )
        return VoiceRatioAnalyzer._nlp

    def analyze(self, work_data: WorkData, context: AnalysisContext) -> AnalysisResult:
        """Count passive vs active sentences via nsubjpass/auxpass deps."""
        nlp = self._get_nlp()
        sentences_text = work_data.sentences_text
        total = len(sentences_text)

        if total == 0:
            return AnalysisResult(
                self.name,
                work_data.work_id,
                {"passive_count": 0.0, "active_count": 0.0, "passive_ratio": 0.0},
                {},
            )

        passive_deps = {"nsubjpass", "auxpass"}
        passive_count = 0
        for doc in nlp.pipe(sentences_text):
            if any(token.dep_ in passive_deps for token in doc):
                passive_count += 1

        active_count = total - passive_count
        return AnalysisResult(
            self.name,
            work_data.work_id,
            {
                "passive_count": float(passive_count),
                "active_count": float(active_count),
                "passive_ratio": passive_count / total,
            },
            {},
        )
