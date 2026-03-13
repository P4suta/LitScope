"""Tests for analysis data models."""

import pytest

from litscope.analysis.models import AnalysisContext, AnalysisResult, WorkData
from litscope.storage.database import Database
from litscope.storage.models import Chapter, Sentence, Token, Work


class TestAnalysisResult:
    def test_frozen(self) -> None:
        result = AnalysisResult(
            analyzer_name="test", work_id="w1", metrics={"a": 1.0}, data={}
        )
        with pytest.raises(AttributeError):
            result.analyzer_name = "other"  # type: ignore[misc]

    def test_fields(self) -> None:
        result = AnalysisResult(
            analyzer_name="vocab",
            work_id="w1",
            metrics={"count": 42.0},
            data={"words": ["a", "b"]},
        )
        assert result.analyzer_name == "vocab"
        assert result.work_id == "w1"
        assert result.metrics == {"count": 42.0}
        assert result.data == {"words": ["a", "b"]}


class TestAnalysisContext:
    def test_set_and_get(self) -> None:
        ctx = AnalysisContext()
        result = AnalysisResult("test", "w1", {}, {})
        ctx.set("test", result)
        assert ctx.get("test") is result

    def test_has(self) -> None:
        ctx = AnalysisContext()
        assert ctx.has("test") is False
        ctx.set("test", AnalysisResult("test", "w1", {}, {}))
        assert ctx.has("test") is True

    def test_get_missing_raises(self) -> None:
        ctx = AnalysisContext()
        with pytest.raises(KeyError):
            ctx.get("missing")


class TestWorkData:
    def test_work_loads(self, work_data: WorkData) -> None:
        assert isinstance(work_data.work, Work)
        assert work_data.work.work_id == "test-work"
        assert work_data.work.title == "Test Title"

    def test_chapters_loads(self, work_data: WorkData) -> None:
        assert len(work_data.chapters) == 2
        assert all(isinstance(c, Chapter) for c in work_data.chapters)
        assert work_data.chapters[0].position == 0

    def test_sentences_loads(self, work_data: WorkData) -> None:
        assert len(work_data.sentences) == 3
        assert all(isinstance(s, Sentence) for s in work_data.sentences)

    def test_tokens_loads(self, work_data: WorkData) -> None:
        assert len(work_data.tokens) == 20
        assert all(isinstance(t, Token) for t in work_data.tokens)

    def test_sentences_text(self, work_data: WorkData) -> None:
        texts = work_data.sentences_text
        assert len(texts) == 3
        assert texts[0] == "The cat sat on the mat."

    def test_cached_property(self, work_data: WorkData) -> None:
        tokens1 = work_data.tokens
        tokens2 = work_data.tokens
        assert tokens1 is tokens2

    def test_work_not_found(self, tmp_db: Database) -> None:
        wd = WorkData(work_id="nonexistent", _db=tmp_db)
        with pytest.raises(ValueError, match="Work not found"):
            _ = wd.work

    # --- SQL pushdown methods ---

    def test_word_frequency_counts(self, work_data: WorkData) -> None:
        counts = work_data.word_frequency_counts
        lemma_dict = dict(counts)
        # cat appears twice (non-stop), should be in results
        assert lemma_dict["cat"] == 2
        # "the" is a stopword — should NOT appear
        assert "the" not in lemma_dict
        # "sit" appears once
        assert lemma_dict["sit"] == 1

    def test_content_token_total(self, work_data: WorkData) -> None:
        # 20 total tokens - 3 PUNCT = 17
        assert work_data.content_token_total == 17

    def test_content_type_count(self, work_data: WorkData) -> None:
        # Non-PUNCT unique lemmas (including stopwords): 13
        assert work_data.content_type_count == 13

    def test_pos_counts(self, work_data: WorkData) -> None:
        counts = dict(work_data.pos_counts)
        assert counts["NOUN"] == 6
        assert counts["DET"] == 4
        assert counts["PUNCT"] == 3

    def test_pos_by_sentence(self, work_data: WorkData) -> None:
        by_sent = work_data.pos_by_sentence
        assert len(by_sent) == 3
        # First sentence: DET NOUN VERB ADP DET NOUN PUNCT
        first_key = "test-work::ch000::s000"
        expected = ["DET", "NOUN", "VERB", "ADP", "DET", "NOUN", "PUNCT"]
        assert by_sent[first_key] == expected

    def test_content_token_texts(self, work_data: WorkData) -> None:
        texts = work_data.content_token_texts
        # 17 non-PUNCT tokens
        assert len(texts) == 17
        assert "." not in texts
        assert "The" in texts

    def test_content_char_total(self, work_data: WorkData) -> None:
        # Sum of len(token) for all non-PUNCT tokens
        expected = sum(len(t) for t in work_data.content_token_texts)
        assert work_data.content_char_total == expected

    def test_content_lemmas(self, work_data: WorkData) -> None:
        lemmas = work_data.content_lemmas
        assert len(lemmas) == 17
        # All lowercased
        assert all(lemma == lemma.lower() for lemma in lemmas)
        # Punctuation excluded
        assert "." not in lemmas
