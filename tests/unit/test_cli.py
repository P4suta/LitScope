"""Tests for CLI commands."""

from pathlib import Path

from click.testing import CliRunner

from litscope.cli.commands import cli
from tests.conftest import create_sample_epub


class TestIngestCommand:
    def test_ingest_success(self, tmp_path: Path) -> None:
        epub_dir = tmp_path / "epubs"
        epub_dir.mkdir()
        create_sample_epub(epub_dir)
        db_path = tmp_path / "test.duckdb"

        result = CliRunner().invoke(
            cli, ["ingest", str(epub_dir), "--db-path", str(db_path)]
        )
        assert result.exit_code == 0
        assert "Ingested: 1" in result.output

    def test_ingest_empty_dir(self, tmp_path: Path) -> None:
        epub_dir = tmp_path / "empty"
        epub_dir.mkdir()
        db_path = tmp_path / "test.duckdb"

        result = CliRunner().invoke(
            cli, ["ingest", str(epub_dir), "--db-path", str(db_path)]
        )
        assert result.exit_code == 0
        assert "Total: 0" in result.output

    def test_ingest_nonexistent_dir(self) -> None:
        result = CliRunner().invoke(cli, ["ingest", "/nonexistent"])
        assert result.exit_code != 0

    def test_ingest_shows_results(self, tmp_path: Path) -> None:
        epub_dir = tmp_path / "epubs"
        epub_dir.mkdir()
        create_sample_epub(epub_dir)
        db_path = tmp_path / "test.duckdb"

        result = CliRunner().invoke(
            cli, ["ingest", str(epub_dir), "--db-path", str(db_path)]
        )
        assert "[OK]" in result.output
        assert "sample" in result.output

    def test_ingest_skip_on_rerun(self, tmp_path: Path) -> None:
        epub_dir = tmp_path / "epubs"
        epub_dir.mkdir()
        create_sample_epub(epub_dir)
        db_path = tmp_path / "test.duckdb"

        CliRunner().invoke(
            cli, ["ingest", str(epub_dir), "--db-path", str(db_path)]
        )
        result = CliRunner().invoke(
            cli, ["ingest", str(epub_dir), "--db-path", str(db_path)]
        )
        assert "Skipped: 1" in result.output
        assert "[SKIP]" in result.output


class TestStatusCommand:
    def test_status_no_db(self, tmp_path: Path) -> None:
        db_path = tmp_path / "nonexistent.duckdb"
        result = CliRunner().invoke(cli, ["status", "--db-path", str(db_path)])
        assert result.exit_code == 0
        assert "not found" in result.output

    def test_status_with_data(self, tmp_path: Path) -> None:
        epub_dir = tmp_path / "epubs"
        epub_dir.mkdir()
        create_sample_epub(epub_dir)
        db_path = tmp_path / "test.duckdb"

        CliRunner().invoke(
            cli, ["ingest", str(epub_dir), "--db-path", str(db_path)]
        )
        result = CliRunner().invoke(cli, ["status", "--db-path", str(db_path)])
        assert result.exit_code == 0
        assert "Works:     1" in result.output
        assert "Chapters:" in result.output


class TestCliGroup:
    def test_version(self) -> None:
        result = CliRunner().invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert "0.1.0" in result.output
