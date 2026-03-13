"""Metadata extractor for Standard Ebooks EPUB files."""

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class WorkMetadata:
    """Extracted metadata for a literary work."""

    title: str
    author: str
    pub_year: int | None = None
    genre: str | None = None
    language: str = "en"


class MetadataExtractor:
    """Extracts structured metadata from raw Dublin Core fields."""

    _YEAR_PATTERN = re.compile(r"\b(\d{4})\b")

    def extract(self, raw_metadata: dict[str, str | list[str]]) -> WorkMetadata:
        """Extract structured WorkMetadata from raw Dublin Core metadata dict."""
        title = self._get_first(raw_metadata.get("title", ""))
        author = self._get_first(raw_metadata.get("creator", ""))
        pub_year = self._extract_year(raw_metadata.get("date"))
        genre = self._get_first(raw_metadata.get("subject")) or None
        language = self._get_first(raw_metadata.get("language", "en"))
        return WorkMetadata(
            title=title,
            author=author,
            pub_year=pub_year,
            genre=genre,
            language=language,
        )

    @staticmethod
    def derive_work_id(file_path: Path | str) -> str:
        """Derive a deterministic work ID from the file path stem."""
        return Path(file_path).stem

    @staticmethod
    def _get_first(value: str | list[str] | None) -> str:
        """Get first element if list, or the value itself."""
        if value is None:
            return ""
        return value[0] if isinstance(value, list) else value

    def _extract_year(self, date_value: str | list[str] | None) -> int | None:
        """Extract a 4-digit year from a date string."""
        text = self._get_first(date_value)
        if not text:
            return None
        match = self._YEAR_PATTERN.search(text)
        return int(match.group(1)) if match else None
