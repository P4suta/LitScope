"""Tests for CLI commands."""

from pathlib import Path
from unittest.mock import patch

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

        CliRunner().invoke(cli, ["ingest", str(epub_dir), "--db-path", str(db_path)])
        result = CliRunner().invoke(
            cli, ["ingest", str(epub_dir), "--db-path", str(db_path)]
        )
        assert "Skipped: 1" in result.output
        assert "[SKIP]" in result.output


    def test_ingest_single_file(self, tmp_path: Path) -> None:
        epub_dir = tmp_path / "epubs"
        epub_dir.mkdir()
        epub_path = create_sample_epub(epub_dir)
        db_path = tmp_path / "test.duckdb"

        result = CliRunner().invoke(
            cli, ["ingest", str(epub_path), "--db-path", str(db_path)]
        )
        assert result.exit_code == 0
        assert "Ingested: 1" in result.output

    def test_ingest_hq_flag(self, tmp_path: Path) -> None:
        epub_dir = tmp_path / "epubs"
        epub_dir.mkdir()
        create_sample_epub(epub_dir)
        db_path = tmp_path / "test.duckdb"

        with patch(
            "litscope.ingestion.pipeline.IngestionPipeline.__init__",
            return_value=None,
        ) as mock_init, patch(
            "litscope.ingestion.pipeline.IngestionPipeline.ingest_directory",
            return_value=__import__(
                "litscope.ingestion.pipeline", fromlist=["IngestionSummary"]
            ).IngestionSummary(),
        ):
            result = CliRunner().invoke(
                cli,
                ["ingest", str(epub_dir), "--hq", "--db-path", str(db_path)],
            )
            assert result.exit_code == 0
            mock_init.assert_called_once()
            _, kwargs = mock_init.call_args
            assert kwargs["model_name"] == "en_core_web_trf"

    def test_ingest_model_option(self, tmp_path: Path) -> None:
        epub_dir = tmp_path / "epubs"
        epub_dir.mkdir()
        create_sample_epub(epub_dir)
        db_path = tmp_path / "test.duckdb"

        with patch(
            "litscope.ingestion.pipeline.IngestionPipeline.__init__",
            return_value=None,
        ) as mock_init, patch(
            "litscope.ingestion.pipeline.IngestionPipeline.ingest_directory",
            return_value=__import__(
                "litscope.ingestion.pipeline", fromlist=["IngestionSummary"]
            ).IngestionSummary(),
        ):
            result = CliRunner().invoke(
                cli,
                [
                    "ingest",
                    str(epub_dir),
                    "--model",
                    "en_core_web_lg",
                    "--db-path",
                    str(db_path),
                ],
            )
            assert result.exit_code == 0
            mock_init.assert_called_once()
            _, kwargs = mock_init.call_args
            assert kwargs["model_name"] == "en_core_web_lg"

    def test_ingest_hq_and_model_mutual_exclusion(self, tmp_path: Path) -> None:
        epub_dir = tmp_path / "epubs"
        epub_dir.mkdir()
        db_path = tmp_path / "test.duckdb"

        result = CliRunner().invoke(
            cli,
            [
                "ingest",
                str(epub_dir),
                "--hq",
                "--model",
                "en_core_web_lg",
                "--db-path",
                str(db_path),
            ],
        )
        assert result.exit_code != 0
        assert "Cannot use both --model and --hq" in result.output


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

        CliRunner().invoke(cli, ["ingest", str(epub_dir), "--db-path", str(db_path)])
        result = CliRunner().invoke(cli, ["status", "--db-path", str(db_path)])
        assert result.exit_code == 0
        assert "Works:     1" in result.output
        assert "Chapters:" in result.output


class TestAnalyzeCommand:
    def test_analyze_success(self, tmp_path: Path) -> None:
        epub_dir = tmp_path / "epubs"
        epub_dir.mkdir()
        create_sample_epub(epub_dir)
        db_path = tmp_path / "test.duckdb"

        CliRunner().invoke(cli, ["ingest", str(epub_dir), "--db-path", str(db_path)])
        result = CliRunner().invoke(
            cli,
            [
                "analyze",
                "--analyzers",
                "vocabulary_frequency",
                "--db-path",
                str(db_path),
            ],
        )
        assert result.exit_code == 0
        assert "Completed:" in result.output
        assert "vocabulary_frequency" in result.output

    def test_analyze_specific_work(self, tmp_path: Path) -> None:
        epub_dir = tmp_path / "epubs"
        epub_dir.mkdir()
        create_sample_epub(epub_dir)
        db_path = tmp_path / "test.duckdb"

        CliRunner().invoke(cli, ["ingest", str(epub_dir), "--db-path", str(db_path)])
        result = CliRunner().invoke(
            cli,
            [
                "analyze",
                "--work",
                "sample",
                "--analyzers",
                "sentence_length",
                "--db-path",
                str(db_path),
            ],
        )
        assert result.exit_code == 0
        assert "[OK] sentence_length" in result.output

    def test_analyze_all_analyzers(self, tmp_path: Path) -> None:
        epub_dir = tmp_path / "epubs"
        epub_dir.mkdir()
        create_sample_epub(epub_dir)
        db_path = tmp_path / "test.duckdb"

        CliRunner().invoke(cli, ["ingest", str(epub_dir), "--db-path", str(db_path)])
        result = CliRunner().invoke(cli, ["analyze", "--db-path", str(db_path)])
        assert result.exit_code == 0
        assert "Completed:" in result.output


class TestServeCommand:
    @patch("uvicorn.run")
    def test_serve_default(self, mock_run, tmp_path: Path) -> None:  # type: ignore[no-untyped-def]
        db_path = tmp_path / "test.duckdb"
        result = CliRunner().invoke(
            cli, ["serve", "--db-path", str(db_path)]
        )
        assert result.exit_code == 0
        mock_run.assert_called_once()
        call_kwargs = mock_run.call_args
        assert call_kwargs[1]["host"] == "0.0.0.0"
        assert call_kwargs[1]["port"] == 8000

    @patch("uvicorn.run")
    def test_serve_custom_host_port(self, mock_run, tmp_path: Path) -> None:  # type: ignore[no-untyped-def]
        db_path = tmp_path / "test.duckdb"
        result = CliRunner().invoke(
            cli,
            ["serve", "--host", "127.0.0.1", "--port", "9000",
             "--db-path", str(db_path)],
        )
        assert result.exit_code == 0
        call_kwargs = mock_run.call_args
        assert call_kwargs[1]["host"] == "127.0.0.1"
        assert call_kwargs[1]["port"] == 9000


class TestCliGroup:
    def test_version(self) -> None:
        result = CliRunner().invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert "0.1.0" in result.output
