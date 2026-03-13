"""Genre comparison endpoints (future)."""

from fastapi import APIRouter, HTTPException

router = APIRouter(tags=["genres"])


@router.get("/genres/comparison")
def genre_comparison() -> None:
    """Genre comparison analysis (not yet implemented)."""
    raise HTTPException(
        status_code=404, detail="Genre comparison not yet implemented"
    )
