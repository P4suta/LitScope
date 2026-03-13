"""Tests for metadata extractor."""

from pathlib import Path

from litscope.ingestion.metadata_extractor import MetadataExtractor, WorkMetadata


class TestMetadataExtractor:
    def test_extract_full_metadata(self) -> None:
        raw = {
            "title": "Pride and Prejudice",
            "creator": "Jane Austen",
            "date": "1813-01-28",
            "subject": "Fiction",
            "language": "en",
        }
        result = MetadataExtractor().extract(raw)
        assert result == WorkMetadata(
            title="Pride and Prejudice",
            author="Jane Austen",
            pub_year=1813,
            genre="Fiction",
            language="en",
        )

    def test_extract_minimal_metadata(self) -> None:
        raw = {"title": "Unknown", "creator": "Anonymous"}
        result = MetadataExtractor().extract(raw)
        assert result.title == "Unknown"
        assert result.author == "Anonymous"
        assert result.pub_year is None
        assert result.genre is None
        assert result.language == "en"

    def test_extract_list_values(self) -> None:
        raw = {
            "title": "Test",
            "creator": "Author",
            "subject": ["Fiction", "Romance"],
        }
        result = MetadataExtractor().extract(raw)
        assert result.genre == "Fiction"

    def test_extract_year_from_full_date(self) -> None:
        raw = {"title": "T", "creator": "A", "date": "1920-01-01"}
        assert MetadataExtractor().extract(raw).pub_year == 1920

    def test_extract_year_from_year_only(self) -> None:
        raw = {"title": "T", "creator": "A", "date": "1984"}
        assert MetadataExtractor().extract(raw).pub_year == 1984

    def test_extract_year_none_when_missing(self) -> None:
        raw = {"title": "T", "creator": "A"}
        assert MetadataExtractor().extract(raw).pub_year is None

    def test_extract_year_none_for_invalid(self) -> None:
        raw = {"title": "T", "creator": "A", "date": "unknown"}
        assert MetadataExtractor().extract(raw).pub_year is None

    def test_empty_metadata(self) -> None:
        result = MetadataExtractor().extract({})
        assert result.title == ""
        assert result.author == ""


class TestDeriveWorkId:
    def test_from_path(self) -> None:
        assert MetadataExtractor.derive_work_id(Path("/data/jane-austen_pride-and-prejudice.epub")) == "jane-austen_pride-and-prejudice"

    def test_from_string(self) -> None:
        assert MetadataExtractor.derive_work_id("books/moby-dick.epub") == "moby-dick"

    def test_strips_extension(self) -> None:
        assert MetadataExtractor.derive_work_id("test.epub") == "test"
