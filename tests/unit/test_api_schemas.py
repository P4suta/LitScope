"""Tests for API Pydantic schemas."""

from litscope.api.schemas.analysis import (
    ComparisonItem,
    POSDistributionItem,
    POSTransitionItem,
    ReadabilityAnalysis,
    SentenceOpeningItem,
    SyntaxAnalysis,
    VocabularyAnalysis,
    WordFrequencyItem,
)
from litscope.api.schemas.common import (
    HealthResponse,
    PaginatedResponse,
    ProblemDetail,
    StatusResponse,
)
from litscope.api.schemas.ingest import IngestRequest, IngestResponse, IngestResultItem
from litscope.api.schemas.works import ChapterInfo, WorkDetail, WorkSummary


class TestCommonSchemas:
    def test_health_response(self) -> None:
        r = HealthResponse(status="ok", version="0.1.0")
        assert r.status == "ok"
        d = r.model_dump()
        assert d["version"] == "0.1.0"

    def test_status_response(self) -> None:
        r = StatusResponse(
            works=5,
            chapters=20,
            sentences=100,
            tokens=500,
            analyzers_available=["a", "b"],
        )
        assert r.works == 5
        assert len(r.analyzers_available) == 2

    def test_problem_detail(self) -> None:
        p = ProblemDetail(title="Not Found", status=404, detail="Work not found")
        assert p.type == "about:blank"
        assert p.status == 404

    def test_paginated_response(self) -> None:
        r = PaginatedResponse[WorkSummary](
            items=[],
            total=0,
            page=1,
            page_size=20,
        )
        assert r.total == 0
        assert r.items == []


class TestWorkSchemas:
    def test_work_summary(self) -> None:
        w = WorkSummary(
            work_id="test",
            title="Test",
            author="Author",
            pub_year=1920,
            genre="Fiction",
            language="en",
            word_count=100,
            sent_count=10,
            chap_count=2,
        )
        assert w.work_id == "test"
        d = w.model_dump()
        assert d["pub_year"] == 1920

    def test_work_summary_nullable_fields(self) -> None:
        w = WorkSummary(
            work_id="t",
            title="T",
            author="A",
            pub_year=None,
            genre=None,
            language="en",
            word_count=None,
            sent_count=None,
            chap_count=None,
        )
        assert w.pub_year is None

    def test_chapter_info(self) -> None:
        c = ChapterInfo(
            chapter_id="ch1",
            position=0,
            title="Chapter 1",
            word_count=50,
            sent_count=5,
        )
        assert c.position == 0

    def test_work_detail(self) -> None:
        w = WorkDetail(
            work_id="test",
            title="Test",
            author="Author",
            pub_year=1920,
            genre="Fiction",
            language="en",
            word_count=100,
            sent_count=10,
            chap_count=2,
            chapters=[],
            analyses_run=["vocabulary_frequency"],
        )
        assert "vocabulary_frequency" in w.analyses_run


class TestAnalysisSchemas:
    def test_word_frequency_item(self) -> None:
        w = WordFrequencyItem(lemma="cat", count=5, tf=0.1)
        assert w.lemma == "cat"

    def test_vocabulary_analysis(self) -> None:
        v = VocabularyAnalysis(
            work_id="t",
            total_tokens=100,
            unique_lemmas=50,
            ttr=0.5,
            hapax_ratio=None,
            yules_k=None,
            mtld=None,
            zipf_alpha=None,
            zipf_r_squared=None,
            zipf_intercept=None,
            top_words=[],
        )
        assert v.ttr == 0.5
        assert v.hapax_ratio is None

    def test_pos_distribution_item(self) -> None:
        p = POSDistributionItem(pos="NOUN", count=10, ratio=0.3)
        assert p.pos == "NOUN"

    def test_pos_transition_item(self) -> None:
        p = POSTransitionItem(from_pos="DET", to_pos="NOUN", count=5, ratio=0.2)
        assert p.from_pos == "DET"

    def test_sentence_opening_item(self) -> None:
        s = SentenceOpeningItem(pattern="DET", count=3, ratio=0.5)
        assert s.pattern == "DET"

    def test_syntax_analysis(self) -> None:
        s = SyntaxAnalysis(
            work_id="t",
            pos_distribution=[],
            pos_transitions=[],
            sentence_openings=[],
            active_voice_count=5,
            passive_voice_count=1,
            passive_ratio=0.17,
        )
        assert s.passive_ratio == 0.17

    def test_syntax_analysis_no_voice(self) -> None:
        s = SyntaxAnalysis(
            work_id="t",
            pos_distribution=[],
            pos_transitions=[],
            sentence_openings=[],
            active_voice_count=None,
            passive_voice_count=None,
            passive_ratio=None,
        )
        assert s.active_voice_count is None

    def test_readability_analysis(self) -> None:
        r = ReadabilityAnalysis(
            work_id="t",
            flesch_kincaid_grade=5.2,
            coleman_liau_index=7.1,
            ari=4.8,
            mean_sentence_length=12.5,
            median_sentence_length=11.0,
            stdev_sentence_length=3.2,
            min_sentence_length=3,
            max_sentence_length=25,
        )
        assert r.flesch_kincaid_grade == 5.2

    def test_readability_analysis_nullable(self) -> None:
        r = ReadabilityAnalysis(
            work_id="t",
            flesch_kincaid_grade=None,
            coleman_liau_index=None,
            ari=None,
            mean_sentence_length=None,
            median_sentence_length=None,
            stdev_sentence_length=None,
            min_sentence_length=None,
            max_sentence_length=None,
        )
        assert r.flesch_kincaid_grade is None

    def test_comparison_item(self) -> None:
        c = ComparisonItem(
            work_id="t",
            title="Test",
            author="Author",
            metrics={"vocabulary_frequency.total_tokens": 100},
        )
        assert c.metrics["vocabulary_frequency.total_tokens"] == 100


class TestIngestSchemas:
    def test_ingest_request(self) -> None:
        r = IngestRequest(epub_dir="path/to/epubs")
        assert r.epub_dir == "path/to/epubs"

    def test_ingest_result_item(self) -> None:
        r = IngestResultItem(
            work_id="test",
            title="Test",
            success=True,
            skipped=False,
            error=None,
        )
        assert r.success is True

    def test_ingest_response(self) -> None:
        r = IngestResponse(total=1, ingested=1, skipped=0, failed=0, results=[])
        assert r.total == 1
