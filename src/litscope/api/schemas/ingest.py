"""Ingest request/response schemas."""

from pydantic import BaseModel


class IngestRequest(BaseModel):
    """Request to ingest EPUBs from a directory."""

    epub_dir: str


class IngestResultItem(BaseModel):
    """Result for a single ingested file."""

    work_id: str
    title: str
    success: bool
    skipped: bool
    error: str | None


class IngestResponse(BaseModel):
    """Ingest pipeline response."""

    total: int
    ingested: int
    skipped: int
    failed: int
    results: list[IngestResultItem]
