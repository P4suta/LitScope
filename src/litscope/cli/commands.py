"""Click CLI entry point for LitScope."""

from pathlib import Path

import click

from litscope.config import get_settings
from litscope.logging import setup_logging
from litscope.storage.database import Database


@click.group()
@click.version_option(package_name="litscope")
def cli() -> None:
    """LitScope — Literary text analysis platform."""


@cli.command()
@click.argument("epub_dir", type=click.Path(exists=True, path_type=Path))
@click.option("--db-path", type=click.Path(path_type=Path), default=None)
def ingest(epub_dir: Path, db_path: Path | None) -> None:
    """Ingest EPUB files from a directory."""
    from litscope.ingestion.pipeline import IngestionPipeline

    settings = get_settings()
    setup_logging(settings.log_level)
    db_path = db_path or settings.db_path

    with Database(db_path) as db:
        db.migrate()
        pipeline = IngestionPipeline(db=db)
        summary = pipeline.ingest_directory(epub_dir)

    click.echo(f"Total: {summary.total}")
    click.echo(f"Ingested: {summary.ingested}")
    click.echo(f"Skipped: {summary.skipped}")
    click.echo(f"Failed: {summary.failed}")

    for result in summary.results:
        status = "SKIP" if result.skipped else ("OK" if result.success else "FAIL")
        click.echo(f"  [{status}] {result.work_id}: {result.title}")


@cli.command()
@click.option("--db-path", type=click.Path(path_type=Path), default=None)
def status(db_path: Path | None) -> None:
    """Show database status."""
    settings = get_settings()
    setup_logging(settings.log_level)
    db_path = db_path or settings.db_path

    if not db_path.exists():
        click.echo("Database not found. Run 'litscope ingest' first.")
        return

    with Database(db_path) as db:
        db.migrate()
        works = db.conn.execute("SELECT COUNT(*) FROM works").fetchone()
        chapters = db.conn.execute("SELECT COUNT(*) FROM chapters").fetchone()
        sentences = db.conn.execute("SELECT COUNT(*) FROM sentences").fetchone()
        tokens = db.conn.execute("SELECT COUNT(*) FROM tokens").fetchone()

    assert works and chapters and sentences and tokens
    click.echo(f"Works:     {works[0]}")
    click.echo(f"Chapters:  {chapters[0]}")
    click.echo(f"Sentences: {sentences[0]}")
    click.echo(f"Tokens:    {tokens[0]}")


@cli.command()
@click.option("--work", default=None, help="Analyze a specific work ID only.")
@click.option(
    "--analyzers", default=None, help="Comma-separated list of analyzer names."
)
@click.option("--db-path", type=click.Path(path_type=Path), default=None)
def analyze(work: str | None, analyzers: str | None, db_path: Path | None) -> None:
    """Run analysis pipeline on ingested works."""
    from litscope.analysis.orchestrator import PipelineOrchestrator
    from litscope.analysis.registry import AnalyzerRegistry

    settings = get_settings()
    setup_logging(settings.log_level)
    db_path = db_path or settings.db_path

    names = [a.strip() for a in analyzers.split(",")] if analyzers else None

    with Database(db_path) as db:
        db.migrate()
        AnalyzerRegistry.discover()
        orchestrator = PipelineOrchestrator(db, settings)

        if work:
            results = orchestrator.run(work, names)
            click.echo(f"Completed: {len(results)} analyzers for {work}")
            for r in results:
                click.echo(f"  [OK] {r.analyzer_name}")
        else:
            all_results = orchestrator.run_all_works(names)
            total_works = len(all_results)
            total_analyzers = sum(len(v) for v in all_results.values())
            click.echo(
                f"Completed: {total_analyzers} analyses across {total_works} works"
            )
            for work_id, results in all_results.items():
                click.echo(f"  {work_id}: {len(results)} analyzers")
                for r in results:
                    click.echo(f"    [OK] {r.analyzer_name}")
