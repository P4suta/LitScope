"""Work-related API schemas."""

from pydantic import BaseModel


class ChapterInfo(BaseModel):
    """Chapter summary within a work."""

    chapter_id: str
    position: int
    title: str | None
    word_count: int | None
    sent_count: int | None


class WorkSummary(BaseModel):
    """Work summary for list endpoints."""

    work_id: str
    title: str
    author: str
    pub_year: int | None
    genre: str | None
    language: str
    word_count: int | None
    sent_count: int | None
    chap_count: int | None


class WorkDetail(WorkSummary):
    """Detailed work info with chapters."""

    chapters: list[ChapterInfo]
    analyses_run: list[str]
