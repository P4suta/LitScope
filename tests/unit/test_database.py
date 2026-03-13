"""Tests for DuckDB database and migration management."""

import pytest

from litscope.exceptions import DatabaseError
from litscope.storage.database import Database


class TestDatabaseConnection:
    def test_connect_and_close(self) -> None:
        db = Database(":memory:")
        db.connect()
        assert db.conn is not None
        db.close()

    def test_conn_raises_when_not_connected(self) -> None:
        db = Database(":memory:")
        with pytest.raises(RuntimeError, match="not connected"):
            _ = db.conn

    def test_context_manager(self) -> None:
        with Database(":memory:") as db:
            result = db.conn.execute("SELECT 1").fetchone()
            assert result == (1,)

    def test_close_when_not_connected(self) -> None:
        db = Database(":memory:")
        db.close()  # Should not raise

    def test_connect_invalid_path_raises_database_error(self) -> None:
        db = Database("/nonexistent/dir/test.duckdb")
        with pytest.raises(DatabaseError, match="Failed to connect"):
            db.connect()


class TestMigration:
    def test_migrate_creates_tables(self) -> None:
        with Database(":memory:") as db:
            db.migrate()
            tables = {
                row[0]
                for row in db.conn.execute(
                    "SELECT table_name FROM information_schema.tables "
                    "WHERE table_schema = 'main'"
                ).fetchall()
            }
            assert {"works", "chapters", "sentences", "tokens", "_migrations"} <= tables

    def test_migrate_idempotent(self) -> None:
        with Database(":memory:") as db:
            db.migrate()
            db.migrate()  # Should not raise
            migrations = db.conn.execute(
                "SELECT name FROM _migrations ORDER BY name"
            ).fetchall()
            assert len(migrations) == 2
            assert migrations[0][0] == "001_initial.sql"
            assert migrations[1][0] == "002_analysis_tables.sql"

    def test_analysis_tables_exist(self) -> None:
        with Database(":memory:") as db:
            db.migrate()
            tables = {
                row[0]
                for row in db.conn.execute(
                    "SELECT table_name FROM information_schema.tables "
                    "WHERE table_schema = 'main'"
                ).fetchall()
            }
            expected = {
                "analysis_results",
                "word_frequencies",
                "pos_distributions",
                "pos_transitions",
                "sentence_opening_patterns",
                "sentiment_scores",
                "character_relations",
                "topics",
                "work_topics",
                "style_features",
                "author_embeddings",
                "ngrams",
                "vocabulary_ages",
                "dialogue_density",
            }
            assert expected <= tables

    def test_insert_and_read_work(self) -> None:
        with Database(":memory:") as db:
            db.migrate()
            db.conn.execute(
                "INSERT INTO works (work_id, title, author, file_path, file_hash) "
                "VALUES (?, ?, ?, ?, ?)",
                ["w1", "Test Title", "Test Author", "/path/to/file.epub", "abc123"],
            )
            row = db.conn.execute(
                "SELECT work_id, title, author FROM works WHERE work_id = ?", ["w1"]
            ).fetchone()
            assert row == ("w1", "Test Title", "Test Author")

    def test_duplicate_pk_raises(self) -> None:
        with Database(":memory:") as db:
            db.migrate()
            db.conn.execute(
                "INSERT INTO works (work_id, title, author, file_path, file_hash) "
                "VALUES (?, ?, ?, ?, ?)",
                ["w1", "Title", "Author", "/path", "hash1"],
            )
            with pytest.raises(Exception):  # noqa: B017
                db.conn.execute(
                    "INSERT INTO works (work_id, title, author, file_path, file_hash) "
                    "VALUES (?, ?, ?, ?, ?)",
                    ["w1", "Title2", "Author2", "/path2", "hash2"],
                )
