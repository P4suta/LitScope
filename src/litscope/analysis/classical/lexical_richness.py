"""Lexical richness analyzer."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from litscope.analysis.base import BaseAnalyzer
from litscope.analysis.models import AnalysisResult

if TYPE_CHECKING:
    from litscope.analysis.models import AnalysisContext, WorkData


class LexicalRichnessAnalyzer(BaseAnalyzer):
    """Compute lexical richness metrics: TTR, hapax ratio, Yule's K, MTLD."""

    name: ClassVar[str] = "lexical_richness"
    dependencies: ClassVar[tuple[str, ...]] = ("vocabulary_frequency",)

    MTLD_THRESHOLD: ClassVar[float] = 0.72

    def analyze(self, work_data: WorkData, context: AnalysisContext) -> AnalysisResult:
        """Compute richness metrics from vocabulary frequency data."""
        vocab_result = context.get("vocabulary_frequency")
        frequencies: dict[str, dict[str, float]] = vocab_result.data["frequencies"]
        total_tokens = int(vocab_result.metrics["total_tokens"])
        total_types = int(vocab_result.metrics["total_types"])

        if total_tokens == 0:
            return AnalysisResult(
                self.name,
                work_data.work_id,
                {"ttr": 0.0, "hapax_ratio": 0.0, "yules_k": 0.0, "mtld": 0.0},
                {},
            )

        ttr = total_types / total_tokens
        hapax_count = sum(1 for f in frequencies.values() if f["count"] == 1)
        hapax_ratio = hapax_count / total_tokens

        # Yule's K
        freq_spectrum: dict[int, int] = {}
        for info in frequencies.values():
            c = int(info["count"])
            freq_spectrum[c] = freq_spectrum.get(c, 0) + 1
        m1 = total_tokens
        m2 = sum(i * i * vi for i, vi in freq_spectrum.items())
        yules_k = 10000 * (m2 - m1) / (m1 * m1) if m1 > 0 else 0.0

        # MTLD
        content_lemmas = [t.lemma.lower() for t in work_data.tokens if t.pos != "PUNCT"]
        mtld = self._compute_mtld(content_lemmas)

        return AnalysisResult(
            self.name,
            work_data.work_id,
            {
                "ttr": ttr,
                "hapax_ratio": hapax_ratio,
                "yules_k": yules_k,
                "mtld": mtld,
            },
            {},
        )

    def _compute_mtld(self, tokens: list[str]) -> float:
        """Compute MTLD (Measure of Textual Lexical Diversity)."""
        forward = self._mtld_one_direction(tokens)
        backward = self._mtld_one_direction(tokens[::-1])
        return (forward + backward) / 2 if (forward + backward) > 0 else 0.0

    def _mtld_one_direction(self, tokens: list[str]) -> float:
        """Compute MTLD in one direction."""
        if not tokens:
            return 0.0
        factors = 0.0
        seen: set[str] = set()
        token_count = 0
        for token in tokens:
            token_count += 1
            seen.add(token)
            ttr = len(seen) / token_count
            if ttr <= self.MTLD_THRESHOLD:
                factors += 1.0
                seen = set()
                token_count = 0
        # Partial factor
        if token_count > 0:
            current_ttr = len(seen) / token_count
            factors += (1.0 - current_ttr) / (1.0 - self.MTLD_THRESHOLD)
        return len(tokens) / factors if factors > 0 else float(len(tokens))
