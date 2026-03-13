"""Shared test fixtures for LitScope."""

from pathlib import Path

import pytest
from ebooklib import epub

from litscope.storage.database import Database


def create_sample_epub(path: Path) -> Path:
    """Create a minimal Standard Ebooks-style EPUB for testing."""
    book = epub.EpubBook()
    book.set_identifier("https://standardebooks.org/ebooks/test-author/test-title")
    book.set_title("Test Title")
    book.set_language("en")
    book.add_author("Test Author")
    book.add_metadata("DC", "date", "1920-01-01")
    book.add_metadata("DC", "subject", "Fiction")

    titlepage = epub.EpubHtml(title="Titlepage", file_name="titlepage.xhtml")
    titlepage.set_content(
        b'<html><body><section epub:type="titlepage">'
        b"<h1>Test Title</h1></section></body></html>"
    )
    book.add_item(titlepage)

    ch1 = epub.EpubHtml(title="Chapter 1", file_name="chapter-1.xhtml")
    ch1.set_content(
        b"<html><body><section>"
        b"<h2>Chapter 1</h2>"
        b"<p>It was a dark and stormy night.</p>"
        b"<p>The wind howled through the trees.</p>"
        b"</section></body></html>"
    )
    book.add_item(ch1)

    ch2 = epub.EpubHtml(title="Chapter 2", file_name="chapter-2.xhtml")
    ch2.set_content(
        b"<html><body><section>"
        b"<h2>Chapter 2</h2>"
        b"<p>Morning came with gentle sunlight.</p>"
        b"</section></body></html>"
    )
    book.add_item(ch2)

    colophon = epub.EpubHtml(title="Colophon", file_name="colophon.xhtml")
    colophon.set_content(
        b'<html><body><section epub:type="colophon">'
        b"<p>Produced by Standard Ebooks.</p></section></body></html>"
    )
    book.add_item(colophon)

    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = [titlepage, ch1, ch2, colophon]

    epub_path = path / "sample.epub"
    epub.write_epub(str(epub_path), book)
    return epub_path


@pytest.fixture
def sample_epub_path(tmp_path: Path) -> Path:
    """Path to a minimal Standard Ebooks-style EPUB fixture."""
    return create_sample_epub(tmp_path)


@pytest.fixture
def tmp_db() -> Database:
    """In-memory DuckDB database with migrations applied."""
    db = Database(":memory:")
    db.connect()
    db.migrate()
    return db
