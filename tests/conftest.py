"""Shared test fixtures for LitScope."""

from pathlib import Path

import pytest
from ebooklib import epub

from litscope.analysis.models import WorkData
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


@pytest.fixture
def seeded_db(tmp_db: Database) -> Database:
    """DB with a sample work: 2 chapters, 3 sentences, ~20 tokens."""
    conn = tmp_db.conn
    conn.execute(
        "INSERT INTO works (work_id, title, author, file_path, file_hash, "
        "pub_year, language, word_count, sent_count, chap_count) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        [
            "test-work",
            "Test Title",
            "Test Author",
            "/path/to/test.epub",
            "abc123hash",
            1920,
            "en",
            20,
            3,
            2,
        ],
    )
    conn.execute(
        "INSERT INTO chapters (chapter_id, work_id, position, title, "
        "word_count, sent_count) VALUES (?, ?, ?, ?, ?, ?)",
        ["test-work::ch000", "test-work", 0, "Chapter 1", 14, 2],
    )
    conn.execute(
        "INSERT INTO chapters (chapter_id, work_id, position, title, "
        "word_count, sent_count) VALUES (?, ?, ?, ?, ?, ?)",
        ["test-work::ch001", "test-work", 1, "Chapter 2", 6, 1],
    )
    conn.execute(
        "INSERT INTO sentences (sentence_id, work_id, chapter_id, position, "
        "text, word_count, char_count) VALUES (?, ?, ?, ?, ?, ?, ?)",
        [
            "test-work::ch000::s000",
            "test-work",
            "test-work::ch000",
            0,
            "The cat sat on the mat.",
            6,
            23,
        ],
    )
    conn.execute(
        "INSERT INTO sentences (sentence_id, work_id, chapter_id, position, "
        "text, word_count, char_count) VALUES (?, ?, ?, ?, ?, ?, ?)",
        [
            "test-work::ch000::s001",
            "test-work",
            "test-work::ch000",
            1,
            "The dog chased the cat quickly.",
            6,
            30,
        ],
    )
    conn.execute(
        "INSERT INTO sentences (sentence_id, work_id, chapter_id, position, "
        "text, word_count, char_count) VALUES (?, ?, ?, ?, ?, ?, ?)",
        [
            "test-work::ch001::s000",
            "test-work",
            "test-work::ch001",
            2,
            "Morning came with gentle sunlight.",
            5,
            34,
        ],
    )
    # Tokens for sentence 1: "The cat sat on the mat."
    tokens_s0 = [
        ("test-work", "test-work::ch000::s000", 0, "The", "the", "DET", True),
        ("test-work", "test-work::ch000::s000", 1, "cat", "cat", "NOUN", False),
        ("test-work", "test-work::ch000::s000", 2, "sat", "sit", "VERB", False),
        ("test-work", "test-work::ch000::s000", 3, "on", "on", "ADP", True),
        ("test-work", "test-work::ch000::s000", 4, "the", "the", "DET", True),
        ("test-work", "test-work::ch000::s000", 5, "mat", "mat", "NOUN", False),
        ("test-work", "test-work::ch000::s000", 6, ".", ".", "PUNCT", False),
    ]
    # Tokens for sentence 2: "The dog chased the cat quickly."
    tokens_s1 = [
        ("test-work", "test-work::ch000::s001", 0, "The", "the", "DET", True),
        ("test-work", "test-work::ch000::s001", 1, "dog", "dog", "NOUN", False),
        ("test-work", "test-work::ch000::s001", 2, "chased", "chase", "VERB", False),
        ("test-work", "test-work::ch000::s001", 3, "the", "the", "DET", True),
        ("test-work", "test-work::ch000::s001", 4, "cat", "cat", "NOUN", False),
        ("test-work", "test-work::ch000::s001", 5, "quickly", "quickly", "ADV", False),
        ("test-work", "test-work::ch000::s001", 6, ".", ".", "PUNCT", False),
    ]
    # Tokens for sentence 3: "Morning came with gentle sunlight."
    tokens_s2 = [
        ("test-work", "test-work::ch001::s000", 0, "Morning", "morning", "NOUN", False),
        ("test-work", "test-work::ch001::s000", 1, "came", "come", "VERB", False),
        ("test-work", "test-work::ch001::s000", 2, "with", "with", "ADP", True),
        ("test-work", "test-work::ch001::s000", 3, "gentle", "gentle", "ADJ", False),
        ("test-work", "test-work::ch001::s000", 4, "sunlight", "sunlight", "NOUN", False),
        ("test-work", "test-work::ch001::s000", 5, ".", ".", "PUNCT", False),
    ]
    conn.executemany(
        "INSERT INTO tokens (work_id, sentence_id, position, token, lemma, pos, is_stop) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        tokens_s0 + tokens_s1 + tokens_s2,
    )
    return tmp_db


@pytest.fixture
def work_data(seeded_db: Database) -> WorkData:
    """WorkData instance for the seeded test work."""
    return WorkData(work_id="test-work", _db=seeded_db)
