"""EPUB parser using ebooklib for Standard Ebooks files."""

import hashlib
from dataclasses import dataclass, field
from pathlib import Path

import ebooklib
import structlog
from ebooklib import epub

from litscope.exceptions import EpubParseError

logger = structlog.get_logger()


_EXCLUDED_EPUB_TYPES = frozenset(
    {
        "titlepage",
        "colophon",
        "toc",
        "loi",
        "copyright-page",
        "cover",
        "frontmatter",
        "backmatter",
    }
)


@dataclass(frozen=True)
class ParsedChapter:
    """A chapter extracted from an EPUB file."""

    title: str | None
    html_content: str
    position: int


@dataclass(frozen=True)
class ParsedEpub:
    """Result of parsing an EPUB file."""

    file_path: str
    file_hash: str
    raw_metadata: dict[str, str | list[str]]
    chapters: list[ParsedChapter] = field(default_factory=list)


class EpubParser:
    """Parses Standard Ebooks EPUB files."""

    def parse(self, epub_path: Path) -> ParsedEpub:
        """Parse an EPUB file and return structured content."""
        try:
            file_hash = self._compute_hash(epub_path)
            book = epub.read_epub(str(epub_path), options={"ignore_ncx": True})
            raw_metadata = self._extract_raw_metadata(book)
            chapters = self._extract_chapters(book)
            logger.info("epub_parsed", path=str(epub_path), chapters=len(chapters))
            return ParsedEpub(
                file_path=str(epub_path),
                file_hash=file_hash,
                raw_metadata=raw_metadata,
                chapters=chapters,
            )
        except EpubParseError:
            raise
        except Exception as e:
            raise EpubParseError(f"Failed to parse {epub_path}: {e}") from e

    @staticmethod
    def _compute_hash(path: Path) -> str:
        """Compute SHA-256 hash of a file."""
        sha256 = hashlib.sha256()
        with path.open("rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    @staticmethod
    def _extract_raw_metadata(book: epub.EpubBook) -> dict[str, str | list[str]]:
        """Extract Dublin Core metadata from OPF."""
        metadata: dict[str, str | list[str]] = {}
        for dc_field in ("title", "creator", "date", "subject", "language"):
            values = book.get_metadata("DC", dc_field)
            if values:
                items = [v[0] for v in values if v[0]]
                metadata[dc_field] = items[0] if len(items) == 1 else items
        return metadata

    @staticmethod
    def _is_excluded(item: epub.EpubHtml) -> bool:
        """Check if an EPUB item should be excluded based on epub:type."""
        content = item.get_content().decode("utf-8", errors="replace")
        return any(
            f'epub:type="{excluded}"' in content for excluded in _EXCLUDED_EPUB_TYPES
        )

    def _extract_chapters(self, book: epub.EpubBook) -> list[ParsedChapter]:
        """Extract body chapters, filtering non-body sections."""
        chapters: list[ParsedChapter] = []
        position = 0
        for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
            if not isinstance(item, epub.EpubHtml) or self._is_excluded(item):
                continue
            content = item.get_content().decode("utf-8", errors="replace")
            title = getattr(item, "title", None) or item.get_name()
            chapters.append(
                ParsedChapter(title=title, html_content=content, position=position)
            )
            position += 1
        return chapters
