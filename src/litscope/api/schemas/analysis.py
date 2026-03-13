"""Analysis result schemas."""

from pydantic import BaseModel


class WordFrequencyItem(BaseModel):
    """Single word frequency entry."""

    lemma: str
    count: int
    tf: float


class VocabularyAnalysis(BaseModel):
    """Vocabulary analysis results."""

    work_id: str
    total_tokens: int
    unique_lemmas: int
    ttr: float | None
    hapax_ratio: float | None
    yules_k: float | None
    mtld: float | None
    zipf_alpha: float | None
    zipf_r_squared: float | None
    zipf_intercept: float | None
    top_words: list[WordFrequencyItem]


class POSDistributionItem(BaseModel):
    """Single POS distribution entry."""

    pos: str
    count: int
    ratio: float


class POSTransitionItem(BaseModel):
    """Single POS transition entry."""

    from_pos: str
    to_pos: str
    count: int
    ratio: float


class SentenceOpeningItem(BaseModel):
    """Single sentence opening pattern entry."""

    pattern: str
    count: int
    ratio: float


class SyntaxAnalysis(BaseModel):
    """Syntax analysis results."""

    work_id: str
    pos_distribution: list[POSDistributionItem]
    pos_transitions: list[POSTransitionItem]
    sentence_openings: list[SentenceOpeningItem]
    active_voice_count: int | None
    passive_voice_count: int | None
    passive_ratio: float | None


class ReadabilityAnalysis(BaseModel):
    """Readability analysis results."""

    work_id: str
    flesch_kincaid_grade: float | None
    coleman_liau_index: float | None
    ari: float | None
    mean_sentence_length: float | None
    median_sentence_length: float | None
    stdev_sentence_length: float | None
    min_sentence_length: int | None
    max_sentence_length: int | None


class ComparisonItem(BaseModel):
    """Per-work metrics for comparison."""

    work_id: str
    title: str
    author: str
    metrics: dict[str, float | None]


class TopicKeyword(BaseModel):
    """Single keyword in a topic."""

    lemma: str
    score: float


class TopicSummary(BaseModel):
    """Topic summary for a work."""

    topic_id: int
    label: str
    work_id: str
    keywords: list[TopicKeyword]


class TimelinePoint(BaseModel):
    """Single point on the vocabulary timeline."""

    pub_year: int
    work_id: str
    title: str
    ttr: float | None
    mtld: float | None
    hapax_ratio: float | None
    unique_lemmas: int | None


class VocabularyTimeline(BaseModel):
    """Vocabulary metrics over publication years."""

    points: list[TimelinePoint]
