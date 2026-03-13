"""Multi-work comparison endpoint."""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, Query

from litscope.api.dependencies import get_db
from litscope.api.schemas.analysis import ComparisonItem
from litscope.exceptions import WorkNotFoundError
from litscope.storage.database import Database  # noqa: TC001

router = APIRouter(tags=["compare"])


@router.get("/compare")
def compare_works(
    db: Database = Depends(get_db),
    work_ids: list[str] = Query(alias="work_id"),
) -> list[ComparisonItem]:
    """Compare metrics across multiple works (max 5)."""
    if len(work_ids) > 5:
        raise HTTPException(
            status_code=400,
            detail="Maximum 5 works can be compared at once",
        )
    results: list[ComparisonItem] = []
    for wid in work_ids:
        row = db.conn.execute(
            "SELECT title, author FROM works WHERE work_id = ?", [wid]
        ).fetchone()
        if row is None:
            raise WorkNotFoundError(wid)

        metrics: dict[str, float | None] = {}
        analysis_rows = db.conn.execute(
            "SELECT analyzer_name, metrics FROM analysis_results WHERE work_id = ?",
            [wid],
        ).fetchall()
        for ar in analysis_rows:
            analyzer_name = ar[0]
            raw = ar[1]
            m = json.loads(raw) if isinstance(raw, str) else dict(raw)
            for k, v in m.items():
                metrics[f"{analyzer_name}.{k}"] = v

        results.append(
            ComparisonItem(work_id=wid, title=row[0], author=row[1], metrics=metrics)
        )

    return results
