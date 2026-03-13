"""Topic extraction endpoints using TF-IDF from word_frequencies."""

from __future__ import annotations

import math

from fastapi import APIRouter, Depends

from litscope.api.dependencies import get_db
from litscope.api.schemas.analysis import TopicKeyword, TopicSummary
from litscope.storage.database import Database  # noqa: TC001

router = APIRouter(tags=["topics"])


@router.get("/topics")
def list_topics(
    db: Database = Depends(get_db),
    top_n: int = 10,
) -> list[TopicSummary]:
    """Extract characteristic keywords per work using TF-IDF scoring."""
    works = db.conn.execute(
        "SELECT work_id, title FROM works ORDER BY title"
    ).fetchall()

    if not works:
        return []

    total_works = len(works)

    # Document frequency: how many works contain each lemma
    df_rows = db.conn.execute(
        "SELECT lemma, COUNT(DISTINCT work_id) AS df "
        "FROM word_frequencies GROUP BY lemma"
    ).fetchall()
    doc_freq = {row[0]: row[1] for row in df_rows}

    results: list[TopicSummary] = []
    for idx, (work_id, title) in enumerate(works):
        wf_rows = db.conn.execute(
            "SELECT lemma, tf FROM word_frequencies WHERE work_id = ? ORDER BY tf DESC",
            [work_id],
        ).fetchall()

        scored = [
            (lemma, tf * math.log(1 + total_works / doc_freq.get(lemma, 1)))
            for lemma, tf in wf_rows
        ]
        scored.sort(key=lambda x: x[1], reverse=True)

        max_score = scored[0][1] if scored else 1.0
        keywords = [
            TopicKeyword(
                lemma=lemma,
                score=round(score / max_score, 3) if max_score > 0 else 0.0,
            )
            for lemma, score in scored[:top_n]
        ]

        results.append(
            TopicSummary(
                topic_id=idx,
                label=title,
                work_id=work_id,
                keywords=keywords,
            )
        )

    return results
