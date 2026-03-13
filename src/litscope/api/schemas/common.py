"""Common API schemas."""

from pydantic import BaseModel


class PaginatedResponse[T](BaseModel):
    """Paginated list response."""

    items: list[T]
    total: int
    page: int
    page_size: int


class ProblemDetail(BaseModel):
    """RFC 7807 problem detail response."""

    type: str = "about:blank"
    title: str
    status: int
    detail: str


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    version: str


class StatusResponse(BaseModel):
    """Corpus status response."""

    works: int
    chapters: int
    sentences: int
    tokens: int
    analyzers_available: list[str]
