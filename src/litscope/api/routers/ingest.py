"""Ingest endpoint."""

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException

from litscope.api.dependencies import get_db
from litscope.api.schemas.ingest import IngestRequest, IngestResponse, IngestResultItem
from litscope.storage.database import Database

router = APIRouter(tags=["ingest"])


@router.post("/ingest")
def ingest_epubs(
    request: IngestRequest, db: Database = Depends(get_db)
) -> IngestResponse:
    """Ingest EPUB files from a directory."""
    from litscope.ingestion.pipeline import IngestionPipeline

    epub_dir = Path(request.epub_dir)
    if not epub_dir.exists():
        raise HTTPException(
            status_code=400, detail=f"Directory not found: {request.epub_dir}"
        )

    pipeline = IngestionPipeline(db=db)
    summary = pipeline.ingest_directory(epub_dir)

    return IngestResponse(
        total=summary.total,
        ingested=summary.ingested,
        skipped=summary.skipped,
        failed=summary.failed,
        results=[
            IngestResultItem(
                work_id=r.work_id,
                title=r.title,
                success=r.success,
                skipped=r.skipped,
                error=r.error,
            )
            for r in summary.results
        ],
    )
