"""Timeline endpoints (future)."""

from fastapi import APIRouter, HTTPException

router = APIRouter(tags=["timeline"])


@router.get("/timeline/vocabulary")
def vocabulary_timeline() -> None:
    """Vocabulary evolution timeline (not yet implemented)."""
    raise HTTPException(status_code=404, detail="Timeline analysis not yet implemented")
