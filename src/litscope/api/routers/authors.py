"""Author-related endpoints."""

from fastapi import APIRouter, Depends, Query

from litscope.api.dependencies import get_db
from litscope.storage.database import Database

router = APIRouter(tags=["authors"])


@router.get("/authors")
def list_authors(
    db: Database = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> dict[str, object]:
    """List distinct authors with work counts."""
    total_row = db.conn.execute("SELECT COUNT(DISTINCT author) FROM works").fetchone()
    total = total_row[0] if total_row else 0

    offset = (page - 1) * page_size
    rows = db.conn.execute(
        "SELECT author, COUNT(*) as work_count FROM works "
        "GROUP BY author ORDER BY author LIMIT ? OFFSET ?",
        [page_size, offset],
    ).fetchall()

    return {
        "items": [{"author": r[0], "work_count": r[1]} for r in rows],
        "total": total,
        "page": page,
        "page_size": page_size,
    }
