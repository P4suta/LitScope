"""Health and status endpoints."""

from fastapi import APIRouter, Depends

from litscope import __version__
from litscope.api.dependencies import get_db
from litscope.api.schemas.common import HealthResponse, StatusResponse
from litscope.storage.database import Database

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> HealthResponse:
    """Health check endpoint."""
    return HealthResponse(status="ok", version=__version__)


@router.get("/status")
def status(db: Database = Depends(get_db)) -> StatusResponse:
    """Corpus status with counts and available analyzers."""
    from litscope.analysis.registry import AnalyzerRegistry

    AnalyzerRegistry.discover()

    conn = db.conn
    works = conn.execute("SELECT COUNT(*) FROM works").fetchone()
    chapters = conn.execute("SELECT COUNT(*) FROM chapters").fetchone()
    sentences = conn.execute("SELECT COUNT(*) FROM sentences").fetchone()
    tokens = conn.execute("SELECT COUNT(*) FROM tokens").fetchone()

    assert works and chapters and sentences and tokens
    return StatusResponse(
        works=works[0],
        chapters=chapters[0],
        sentences=sentences[0],
        tokens=tokens[0],
        analyzers_available=AnalyzerRegistry.all_names(),
    )
