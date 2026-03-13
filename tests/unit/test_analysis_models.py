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
