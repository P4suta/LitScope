"""Differential ingestion pipeline orchestrating parsing, extraction, and normalization."""

from dataclasses import dataclass, field
from pathlib import Path

import structlog

from litscope.ingestion.epub_parser import EpubParser
from litscope.ingestion.metadata_extractor import MetadataExtractor
from litscope.ingestion.text_normalizer import TextNormalizer
from litscope.storage.database import Database

logger = structlog.get_logger()


@dataclass(frozen=True)
class IngestionResult:
    """Result of ingesting a single EPUB file."""

    work_id: str
    title: str
    success: bool
    skipped: bool = False
    error: str | None = None
    chapters: int = 0
    sentences: int = 0
    tokens: int = 0


@dataclass(frozen=True)
class IngestionSummary:
    """Summary of a batch ingestion run."""

    results: list[IngestionResult] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.results)

    @property
    def ingested(self) -> int:
        return sum(1 for r in self.results if r.success and not r.skipped)

    @property
    def skipped(self) -> int:
        return sum(1 for r in self.results if r.skipped)

    @property
    def failed(self) -> int:
        return sum(1 for r in self.results if not r.success)


class IngestionPipeline:
    """Orchestrates EPUB ingestion: parse → extract metadata → normalize → store."""

    def __init__(
        self,
        db: Database,
        parser: EpubParser | None = None,
        extractor: MetadataExtractor | None = None,
        normalizer: TextNormalizer | None = None,
    ) -> None:
        self._db = db
        self._parser = parser or EpubParser()
        self._extractor = extractor or MetadataExtractor()
        self._normalizer = normalizer or TextNormalizer()

    def ingest_directory(self, epub_dir: Path) -> IngestionSummary:
        """Ingest all EPUB files in a directory."""
        epub_files = sorted(epub_dir.glob("*.epub"))
        results = [self._ingest_one(f) for f in epub_files]
        return IngestionSummary(results=results)

    def _ingest_one(self, epub_path: Path) -> IngestionResult:
        """Ingest a single EPUB file with error isolation."""
        work_id = self._extractor.derive_work_id(epub_path)
        try:
            return self._do_ingest(epub_path, work_id)
        except Exception as e:
            logger.error("ingestion_failed", work_id=work_id, error=str(e))
            return IngestionResult(
                work_id=work_id, title="", success=False, error=str(e)
            )

    def _do_ingest(self, epub_path: Path, work_id: str) -> IngestionResult:
        """Core ingestion logic for a single EPUB."""
        parsed = self._parser.parse(epub_path)

        # Differential skip
        existing_hash = self._get_existing_hash(work_id)
        if existing_hash == parsed.file_hash:
            logger.info("ingestion_skipped", work_id=work_id)
            return IngestionResult(
                work_id=work_id,
                title=str(parsed.raw_metadata.get("title", "")),
                success=True,
                skipped=True,
            )

        metadata = self._extractor.extract(parsed.raw_metadata)

        # Normalize all chapters
        normalized_chapters = [
            (ch, self._normalizer.normalize(ch.html_content))
            for ch in parsed.chapters
        ]

        total_sentences = 0
        total_tokens = 0
        conn = self._db.conn

        # Delete existing data for re-ingestion
        if existing_hash is not None:
            self._delete_work(work_id)

        # Insert work
        total_words = sum(nc.word_count for _, nc in normalized_chapters)
        total_sents = sum(nc.sent_count for _, nc in normalized_chapters)
        conn.execute(
            "INSERT INTO works (work_id, title, author, pub_year, genre, language, "
            "word_count, sent_count, chap_count, file_path, file_hash) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [
                work_id,
                metadata.title,
                metadata.author,
                metadata.pub_year,
                metadata.genre,
                metadata.language,
                total_words,
                total_sents,
                len(normalized_chapters),
                str(epub_path),
                parsed.file_hash,
            ],
        )

        # Insert chapters, sentences, tokens
        for parsed_ch, norm_ch in normalized_chapters:
            chapter_id = f"{work_id}::ch{parsed_ch.position:03d}"
            conn.execute(
                "INSERT INTO chapters (chapter_id, work_id, position, title, "
                "word_count, sent_count) VALUES (?, ?, ?, ?, ?, ?)",
                [
                    chapter_id,
                    work_id,
                    parsed_ch.position,
                    parsed_ch.title,
                    norm_ch.word_count,
                    norm_ch.sent_count,
                ],
            )

            sent_global_pos = total_sentences
            for sent_idx, sent in enumerate(norm_ch.sentences):
                sentence_id = f"{chapter_id}::s{sent_global_pos + sent_idx:05d}"
                conn.execute(
                    "INSERT INTO sentences (sentence_id, work_id, chapter_id, "
                    "position, text, word_count, char_count) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?)",
                    [
                        sentence_id,
                        work_id,
                        chapter_id,
                        sent_global_pos + sent_idx,
                        sent.text,
                        sent.word_count,
                        sent.char_count,
                    ],
                )

                if sent.tokens:
                    conn.executemany(
                        "INSERT INTO tokens (work_id, sentence_id, position, "
                        "token, lemma, pos, is_stop) "
                        "VALUES (?, ?, ?, ?, ?, ?, ?)",
                        [
                            (
                                work_id,
                                sentence_id,
                                tok_idx,
                                tok.text,
                                tok.lemma,
                                tok.pos,
                                tok.is_stop,
                            )
                            for tok_idx, tok in enumerate(sent.tokens)
                        ],
                    )
                    total_tokens += len(sent.tokens)

            total_sentences += len(norm_ch.sentences)

        logger.info(
            "ingestion_complete",
            work_id=work_id,
            chapters=len(normalized_chapters),
            sentences=total_sentences,
            tokens=total_tokens,
        )
        return IngestionResult(
            work_id=work_id,
            title=metadata.title,
            success=True,
            chapters=len(normalized_chapters),
            sentences=total_sentences,
            tokens=total_tokens,
        )

    def _get_existing_hash(self, work_id: str) -> str | None:
        """Get the stored file hash for a work, or None if not found."""
        row = self._db.conn.execute(
            "SELECT file_hash FROM works WHERE work_id = ?", [work_id]
        ).fetchone()
        return row[0] if row else None

    def _delete_work(self, work_id: str) -> None:
        """Delete all data for a work (for re-ingestion)."""
        conn = self._db.conn
        conn.execute("DELETE FROM tokens WHERE work_id = ?", [work_id])
        conn.execute("DELETE FROM sentences WHERE work_id = ?", [work_id])
        conn.execute("DELETE FROM chapters WHERE work_id = ?", [work_id])
        conn.execute("DELETE FROM works WHERE work_id = ?", [work_id])
