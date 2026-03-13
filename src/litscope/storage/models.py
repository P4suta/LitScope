"""Frozen dataclasses for core data models."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Work:
    """A literary work ingested from an EPUB file."""

    work_id: str
    title: str
    author: str
    file_path: str
    file_hash: str
    pub_year: int | None = None
    genre: str | None = None
    language: str = "en"
    word_count: int | None = None
    sent_count: int | None = None
    chap_count: int | None = None
    ingested_at: datetime | None = None


@dataclass(frozen=True)
class Chapter:
    """A chapter within a work."""

    chapter_id: str
    work_id: str
    position: int
    title: str | None = None
    word_count: int | None = None
    sent_count: int | None = None


@dataclass(frozen=True)
class Sentence:
    """A sentence within a chapter."""

    sentence_id: str
    work_id: str
    chapter_id: str
    position: int
    text: str
    word_count: int | None = None
    char_count: int | None = None


@dataclass(frozen=True)
class Token:
    """A token within a sentence."""

    work_id: str
    sentence_id: str
    position: int
    token: str
    lemma: str
    pos: str
    is_stop: bool = False
