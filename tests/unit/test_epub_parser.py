"""Tests for EPUB parser."""

import hashlib
from pathlib import Path

import pytest

from litscope.exceptions import EpubParseError
from litscope.ingestion.epub_parser import EpubParser, ParsedChapter, ParsedEpub


class TestEpubParser:
    def test_parse_returns_parsed_epub(self, sample_epub_path: Path) -> None:
        result = EpubParser().parse(sample_epub_path)
        assert isinstance(result, ParsedEpub)

    def test_file_hash_is_sha256(self, sample_epub_path: Path) -> None:
        result = EpubParser().parse(sample_epub_path)
        expected = hashlib.sha256(sample_epub_path.read_bytes()).hexdigest()
        assert result.file_hash == expected

    def test_file_path_stored(self, sample_epub_path: Path) -> None:
        result = EpubParser().parse(sample_epub_path)
        assert result.file_path == str(sample_epub_path)

    def test_metadata_extraction(self, sample_epub_path: Path) -> None:
        result = EpubParser().parse(sample_epub_path)
        assert result.raw_metadata["title"] == "Test Title"
        assert result.raw_metadata["creator"] == "Test Author"
        assert result.raw_metadata["language"] == "en"
        assert result.raw_metadata["subject"] == "Fiction"

    def test_chapters_exclude_titlepage_and_colophon(
        self, sample_epub_path: Path
    ) -> None:
        result = EpubParser().parse(sample_epub_path)
        assert len(result.chapters) == 2

    def test_chapter_content_is_html(self, sample_epub_path: Path) -> None:
        result = EpubParser().parse(sample_epub_path)
        assert "<p>" in result.chapters[0].html_content

    def test_chapter_positions_sequential(self, sample_epub_path: Path) -> None:
        result = EpubParser().parse(sample_epub_path)
        positions = [ch.position for ch in result.chapters]
        assert positions == [0, 1]

    def test_parsed_chapter_dataclass(self) -> None:
        ch = ParsedChapter(title="Ch1", html_content="<p>text</p>", position=0)
        assert ch.title == "Ch1"
        assert ch.position == 0

    def test_date_metadata(self, sample_epub_path: Path) -> None:
        result = EpubParser().parse(sample_epub_path)
        assert "date" in result.raw_metadata

    def test_invalid_epub_raises_parse_error(self, tmp_path: Path) -> None:
        bad = tmp_path / "bad.epub"
        bad.write_bytes(b"not an epub")
        with pytest.raises(EpubParseError, match="Failed to parse"):
            EpubParser().parse(bad)
