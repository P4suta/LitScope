"""Ingest request/response schemas."""

from pathlib import PurePosixPath

from pydantic import BaseModel, field_validator


class IngestRequest(BaseModel):
    """Request to ingest EPUBs from a directory."""

    epub_dir: str

    @field_validator("epub_dir")
    @classmethod
    def reject_path_traversal(cls, v: str) -> str:
        """Reject absolute paths and parent-directory references."""
        if PurePosixPath(v).is_absolute() or ".." in PurePosixPath(v).parts:
            msg = "Path must be relative and must not contain '..'"
            raise ValueError(msg)
        return v


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
