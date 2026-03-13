"""Topic modeling endpoints (future)."""

from fastapi import APIRouter, HTTPException

router = APIRouter(tags=["topics"])


@router.get("/topics")
def list_topics() -> None:
    """List discovered topics (not yet implemented)."""
    raise HTTPException(status_code=404, detail="Topic analysis not yet implemented")
