"""Work listing and analysis endpoints."""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, Query

from litscope.api.dependencies import get_db
from litscope.api.schemas.analysis import (
    POSDistributionItem,
    POSTransitionItem,
    ReadabilityAnalysis,
    SentenceOpeningItem,
    SyntaxAnalysis,
    VocabularyAnalysis,
    WordFrequencyItem,
)
from litscope.api.schemas.common import PaginatedResponse
from litscope.api.schemas.works import ChapterInfo, WorkDetail, WorkSummary
from litscope.exceptions import WorkNotFoundError
from litscope.storage.database import Database  # noqa: TC001

router = APIRouter(tags=["works"])


def _get_analysis_metrics(
    db: Database, work_id: str, analyzer_name: str
) -> dict[str, float] | None:
    """Fetch metrics dict for a given analyzer/work, or None if not run."""
    row = db.conn.execute(
        "SELECT metrics FROM analysis_results WHERE analyzer_name = ? AND work_id = ?",
        [analyzer_name, work_id],
    ).fetchone()
    if row is None:
        return None
    raw = row[0]
    return json.loads(raw) if isinstance(raw, str) else dict(raw)


@router.get("/works")
def list_works(
    db: Database = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    author: str | None = None,
    genre: str | None = None,
    search: str | None = None,
) -> PaginatedResponse[WorkSummary]:
    """List works with pagination and filtering."""
    conditions: list[str] = []
    params: list[str | int] = []

    if author:
        conditions.append("author = ?")
        params.append(author)
    if genre:
        conditions.append("genre = ?")
        params.append(genre)
    if search:
        conditions.append("(title ILIKE ? OR author ILIKE ?)")
        params.extend([f"%{search}%", f"%{search}%"])

    where = f" WHERE {' AND '.join(conditions)}" if conditions else ""
    total_row = db.conn.execute(f"SELECT COUNT(*) FROM works{where}", params).fetchone()
    total = total_row[0] if total_row else 0

    offset = (page - 1) * page_size
    rows = db.conn.execute(
        "SELECT work_id, title, author, pub_year, genre, language, "
        f"word_count, sent_count, chap_count FROM works{where} "
        f"ORDER BY title LIMIT ? OFFSET ?",
        [*params, page_size, offset],
    ).fetchall()

    items = [
        WorkSummary(
            work_id=r[0],
            title=r[1],
            author=r[2],
            pub_year=r[3],
            genre=r[4],
            language=r[5],
            word_count=r[6],
            sent_count=r[7],
            chap_count=r[8],
        )
        for r in rows
    ]
    return PaginatedResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/works/{work_id}")
def get_work(work_id: str, db: Database = Depends(get_db)) -> WorkDetail:
    """Get detailed work info including chapters and analyses run."""
    row = db.conn.execute(
        "SELECT work_id, title, author, pub_year, genre, language, "
        "word_count, sent_count, chap_count FROM works WHERE work_id = ?",
        [work_id],
    ).fetchone()
    if row is None:
        raise WorkNotFoundError(work_id)

    chapters = db.conn.execute(
        "SELECT chapter_id, position, title, word_count, sent_count "
        "FROM chapters WHERE work_id = ? ORDER BY position",
        [work_id],
    ).fetchall()

    analyses = db.conn.execute(
        "SELECT DISTINCT analyzer_name FROM analysis_results WHERE work_id = ?",
        [work_id],
    ).fetchall()

    return WorkDetail(
        work_id=row[0],
        title=row[1],
        author=row[2],
        pub_year=row[3],
        genre=row[4],
        language=row[5],
        word_count=row[6],
        sent_count=row[7],
        chap_count=row[8],
        chapters=[
            ChapterInfo(
                chapter_id=c[0],
                position=c[1],
                title=c[2],
                word_count=c[3],
                sent_count=c[4],
            )
            for c in chapters
        ],
        analyses_run=sorted(a[0] for a in analyses),
    )


@router.get("/works/{work_id}/vocabulary")
def get_vocabulary(
    work_id: str,
    db: Database = Depends(get_db),
    top_n: int = Query(50, ge=1, le=500),
) -> VocabularyAnalysis:
    """Get vocabulary analysis for a work."""
    _assert_work_exists(db, work_id)
    vocab = _get_analysis_metrics(db, work_id, "vocabulary_frequency")
    if vocab is None:
        raise HTTPException(
            status_code=404,
            detail="Vocabulary analysis not run for this work",
        )

    richness = _get_analysis_metrics(db, work_id, "lexical_richness")
    zipf = _get_analysis_metrics(db, work_id, "zipf_fitness")

    words = db.conn.execute(
        "SELECT lemma, count, tf FROM word_frequencies "
        "WHERE work_id = ? ORDER BY count DESC LIMIT ?",
        [work_id, top_n],
    ).fetchall()

    return VocabularyAnalysis(
        work_id=work_id,
        total_tokens=int(vocab.get("total_tokens", 0)),
        unique_lemmas=int(vocab.get("total_types", 0)),
        ttr=richness.get("ttr") if richness else None,
        hapax_ratio=richness.get("hapax_ratio") if richness else None,
        yules_k=richness.get("yules_k") if richness else None,
        mtld=richness.get("mtld") if richness else None,
        zipf_alpha=zipf.get("alpha") if zipf else None,
        zipf_r_squared=zipf.get("r_squared") if zipf else None,
        zipf_intercept=zipf.get("intercept") if zipf else None,
        top_words=[WordFrequencyItem(lemma=w[0], count=w[1], tf=w[2]) for w in words],
    )


@router.get("/works/{work_id}/syntax")
def get_syntax(work_id: str, db: Database = Depends(get_db)) -> SyntaxAnalysis:
    """Get syntax analysis for a work."""
    _assert_work_exists(db, work_id)
    pos_dist = _get_analysis_metrics(db, work_id, "pos_distribution")
    if pos_dist is None:
        raise HTTPException(
            status_code=404,
            detail="Syntax analysis not run for this work",
        )

    pos_rows = db.conn.execute(
        "SELECT pos, count, ratio FROM pos_distributions "
        "WHERE work_id = ? ORDER BY count DESC",
        [work_id],
    ).fetchall()

    trans_rows = db.conn.execute(
        "SELECT from_pos, to_pos, count, ratio FROM pos_transitions "
        "WHERE work_id = ? ORDER BY count DESC",
        [work_id],
    ).fetchall()

    opening_rows = db.conn.execute(
        "SELECT pattern, count, ratio FROM sentence_opening_patterns "
        "WHERE work_id = ? ORDER BY count DESC",
        [work_id],
    ).fetchall()

    voice = _get_analysis_metrics(db, work_id, "voice_ratio")

    return SyntaxAnalysis(
        work_id=work_id,
        pos_distribution=[
            POSDistributionItem(pos=r[0], count=r[1], ratio=r[2]) for r in pos_rows
        ],
        pos_transitions=[
            POSTransitionItem(from_pos=r[0], to_pos=r[1], count=r[2], ratio=r[3])
            for r in trans_rows
        ],
        sentence_openings=[
            SentenceOpeningItem(pattern=r[0], count=r[1], ratio=r[2])
            for r in opening_rows
        ],
        active_voice_count=(int(voice["active_count"]) if voice else None),
        passive_voice_count=(int(voice["passive_count"]) if voice else None),
        passive_ratio=voice.get("passive_ratio") if voice else None,
    )


@router.get("/works/{work_id}/readability")
def get_readability(
    work_id: str, db: Database = Depends(get_db)
) -> ReadabilityAnalysis:
    """Get readability analysis for a work."""
    _assert_work_exists(db, work_id)
    readability = _get_analysis_metrics(db, work_id, "readability")
    if readability is None:
        raise HTTPException(
            status_code=404,
            detail="Readability analysis not run for this work",
        )

    sent_len = _get_analysis_metrics(db, work_id, "sentence_length")

    return ReadabilityAnalysis(
        work_id=work_id,
        flesch_kincaid_grade=readability.get("flesch_kincaid_grade"),
        coleman_liau_index=readability.get("coleman_liau_index"),
        ari=readability.get("ari"),
        mean_sentence_length=(sent_len.get("mean") if sent_len else None),
        median_sentence_length=(sent_len.get("median") if sent_len else None),
        stdev_sentence_length=(sent_len.get("stdev") if sent_len else None),
        min_sentence_length=(
            int(sent_len["min"]) if sent_len and "min" in sent_len else None
        ),
        max_sentence_length=(
            int(sent_len["max"]) if sent_len and "max" in sent_len else None
        ),
    )


_FUTURE_ANALYSES = [
    "sentiment",
    "characters",
    "dialogue",
    "ngrams",
    "stylometry",
]


def _make_future_stub(name: str):  # type: ignore[no-untyped-def]
    """Create a stub endpoint that returns 404 for unimplemented analyses."""

    async def stub(work_id: str, db: Database = Depends(get_db)) -> None:
        _assert_work_exists(db, work_id)
        raise HTTPException(
            status_code=404,
            detail=f"{name.title()} analysis not yet implemented",
        )

    stub.__name__ = f"get_{name}"
    stub.__qualname__ = f"get_{name}"
    return stub


for _name in _FUTURE_ANALYSES:
    router.add_api_route(
        f"/works/{{work_id}}/{_name}",
        _make_future_stub(_name),
        methods=["GET"],
        tags=["works"],
    )


def _assert_work_exists(db: Database, work_id: str) -> None:
    """Raise WorkNotFoundError if work does not exist."""
    row = db.conn.execute("SELECT 1 FROM works WHERE work_id = ?", [work_id]).fetchone()
    if row is None:
        raise WorkNotFoundError(work_id)
