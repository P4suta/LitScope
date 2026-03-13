"""Timeline endpoints for vocabulary evolution over publication years."""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends

from litscope.api.dependencies import get_db
from litscope.api.schemas.analysis import TimelinePoint, VocabularyTimeline
from litscope.storage.database import Database  # noqa: TC001

router = APIRouter(tags=["timeline"])


@router.get("/timeline/vocabulary")
def vocabulary_timeline(
    db: Database = Depends(get_db),
) -> VocabularyTimeline:
    """Vocabulary metrics per work, ordered by publication year."""
    rows = db.conn.execute(
        "SELECT w.work_id, w.title, w.pub_year "
        "FROM works w "
        "WHERE w.pub_year IS NOT NULL "
        "ORDER BY w.pub_year, w.title"
    ).fetchall()

    points: list[TimelinePoint] = []
    for work_id, title, pub_year in rows:
        ttr: float | None = None
        mtld: float | None = None
        hapax_ratio: float | None = None
        unique_lemmas: int | None = None

        # lexical_richness metrics
        lr_row = db.conn.execute(
            "SELECT metrics FROM analysis_results "
            "WHERE work_id = ? AND analyzer_name = 'lexical_richness'",
            [work_id],
        ).fetchone()
        if lr_row:
            m = json.loads(lr_row[0]) if isinstance(lr_row[0], str) else dict(lr_row[0])
            ttr = m.get("ttr")
            mtld = m.get("mtld")
            hapax_ratio = m.get("hapax_ratio")

        # vocabulary_frequency metrics
        vf_row = db.conn.execute(
            "SELECT metrics FROM analysis_results "
            "WHERE work_id = ? AND analyzer_name = 'vocabulary_frequency'",
            [work_id],
        ).fetchone()
        if vf_row:
            m = json.loads(vf_row[0]) if isinstance(vf_row[0], str) else dict(vf_row[0])
            unique_lemmas = m.get("total_types")

        points.append(
            TimelinePoint(
                pub_year=pub_year,
                work_id=work_id,
                title=title,
                ttr=ttr,
                mtld=mtld,
                hapax_ratio=hapax_ratio,
                unique_lemmas=unique_lemmas,
            )
        )

    return VocabularyTimeline(points=points)
