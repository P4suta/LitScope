"""Data models for the analysis framework."""

from __future__ import annotations

from dataclasses import dataclass, field
from functools import cached_property
from typing import Any

from litscope.storage.database import Database
from litscope.storage.models import Chapter, Sentence, Token, Work


@dataclass(frozen=True)
class AnalysisResult:
    """Immutable result from an analyzer."""

    analyzer_name: str
    work_id: str
    metrics: dict[str, float]
    data: dict[str, Any]


class AnalysisContext:
    """Shared context for passing data between dependent analyzers within a run."""

    def __init__(self) -> None:
        self._store: dict[str, AnalysisResult] = {}

    def set(self, name: str, result: AnalysisResult) -> None:
        """Store an analysis result by analyzer name."""
        self._store[name] = result

    def get(self, name: str) -> AnalysisResult:
        """Retrieve a stored result, raising KeyError if not found."""
        return self._store[name]

    def has(self, name: str) -> bool:
        """Check if a result exists for the given analyzer name."""
        return name in self._store


@dataclass
class WorkData:
    """Lazy-loading accessor for a work's data from the database."""

    work_id: str
    _db: Database = field(repr=False)

    @cached_property
    def work(self) -> Work:
        """Load work metadata from the database."""
        row = self._db.conn.execute(
            "SELECT work_id, title, author, file_path, file_hash, "
            "pub_year, genre, language, word_count, sent_count, chap_count, ingested_at "
            "FROM works WHERE work_id = ?",
            [self.work_id],
        ).fetchone()
        if row is None:
            msg = f"Work not found: {self.work_id}"
            raise ValueError(msg)
        return Work(*row)

    @cached_property
    def chapters(self) -> list[Chapter]:
        """Load chapters ordered by position."""
        rows = self._db.conn.execute(
            "SELECT chapter_id, work_id, position, title, word_count, sent_count "
            "FROM chapters WHERE work_id = ? ORDER BY position",
            [self.work_id],
        ).fetchall()
        return [Chapter(*row) for row in rows]

    @cached_property
    def sentences(self) -> list[Sentence]:
        """Load sentences ordered by position."""
        rows = self._db.conn.execute(
            "SELECT sentence_id, work_id, chapter_id, position, text, "
            "word_count, char_count "
            "FROM sentences WHERE work_id = ? ORDER BY position",
            [self.work_id],
        ).fetchall()
        return [Sentence(*row) for row in rows]

    @cached_property
    def tokens(self) -> list[Token]:
        """Load all tokens for the work."""
        rows = self._db.conn.execute(
            "SELECT work_id, sentence_id, position, token, lemma, pos, is_stop "
            "FROM tokens WHERE work_id = ? ORDER BY sentence_id, position",
            [self.work_id],
        ).fetchall()
        return [Token(*row) for row in rows]

    @cached_property
    def sentences_text(self) -> list[str]:
        """Load sentence texts as a flat list."""
        return [s.text for s in self.sentences]
