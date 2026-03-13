"""Pipeline orchestrator for running analyzers in dependency order."""

from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import TYPE_CHECKING

import structlog

from litscope.analysis.models import AnalysisContext, WorkData
from litscope.analysis.registry import AnalyzerRegistry

if TYPE_CHECKING:
    from litscope.analysis.models import AnalysisResult
    from litscope.config import LitScopeSettings
    from litscope.storage.database import Database

logger = structlog.get_logger()


@dataclass(frozen=True)
class AnalyzerTiming:
    """Timing data for a single analyzer execution."""

    analyzer_name: str
    work_id: str
    analyze_seconds: float
    store_seconds: float
    total_seconds: float


def _build_layers(order: list[str]) -> list[list[str]]:
    """Group analyzers into parallelizable layers by dependency depth."""
    completed: set[str] = set()
    layers: list[list[str]] = []
    remaining = list(order)
    while remaining:
        layer = [
            name
            for name in remaining
            if all(dep in completed for dep in AnalyzerRegistry.get(name).dependencies)
        ]
        layers.append(layer)
        completed.update(layer)
        remaining = [n for n in remaining if n not in completed]
    return layers


class PipelineOrchestrator:
    """Orchestrates analyzer execution in dependency order."""

    def __init__(self, db: Database, settings: LitScopeSettings) -> None:
        self._db = db
        self._settings = settings
        self._last_timings: list[AnalyzerTiming] = []
        self._all_timings: dict[str, list[AnalyzerTiming]] = {}

    def run(
        self,
        work_id: str,
        names: list[str] | None = None,
        *,
        force: bool = False,
        parallel: bool = False,
    ) -> list[AnalysisResult]:
        """Run analyzers for a single work in dependency order."""
        order = AnalyzerRegistry.resolve_order(names)
        work_data = WorkData(work_id=work_id, _db=self._db)
        context = AnalysisContext()
        results: list[AnalysisResult] = []
        failed: set[str] = set()
        self._last_timings = []

        if parallel:
            return self._run_parallel(
                work_id, order, work_data, context, results, failed, force=force
            )
        return self._run_sequential(
            work_id, order, work_data, context, results, failed, force=force
        )

    def _run_sequential(
        self,
        work_id: str,
        order: list[str],
        work_data: WorkData,
        context: AnalysisContext,
        results: list[AnalysisResult],
        failed: set[str],
        *,
        force: bool,
    ) -> list[AnalysisResult]:
        for analyzer_name in order:
            self._run_one(
                analyzer_name, work_id, work_data, context, results, failed, force=force
            )
        return results

    def _run_parallel(
        self,
        work_id: str,
        order: list[str],
        work_data: WorkData,
        context: AnalysisContext,
        results: list[AnalysisResult],
        failed: set[str],
        *,
        force: bool,
    ) -> list[AnalysisResult]:
        """Run analyzers in parallel layers."""
        layers = _build_layers(order)
        for layer in layers:
            if len(layer) == 1:
                self._run_one(
                    layer[0], work_id, work_data, context, results, failed, force=force
                )
            else:
                self._run_layer_parallel(
                    layer, work_id, work_data, context, results, failed, force=force
                )
        return results

    def _run_layer_parallel(
        self,
        layer: list[str],
        work_id: str,
        work_data: WorkData,
        context: AnalysisContext,
        results: list[AnalysisResult],
        failed: set[str],
        *,
        force: bool,
    ) -> None:
        """Run a single layer of independent analyzers in parallel."""

        def _analyze_one(
            analyzer_name: str,
        ) -> tuple[str, AnalysisResult | None, float, Exception | None]:
            """Run analyze() only (no store) — thread-safe."""
            try:
                analyzer_cls = AnalyzerRegistry.get(analyzer_name)
                analyzer = analyzer_cls(self._db, self._settings)
                t0 = time.perf_counter()
                result = analyzer.analyze(work_data, context)
                elapsed = time.perf_counter() - t0
                return analyzer_name, result, elapsed, None
            except Exception as exc:
                return analyzer_name, None, 0.0, exc

        # Pre-warm WorkData caches to avoid concurrent DB access
        _prewarm_work_data(work_data)

        # Check skippable analyzers on main thread (DB access not thread-safe)
        to_run: list[str] = []
        for analyzer_name in layer:
            analyzer_cls = AnalyzerRegistry.get(analyzer_name)
            if any(dep in failed for dep in analyzer_cls.dependencies):
                logger.warning(
                    "skipping_analyzer",
                    analyzer=analyzer_name,
                    reason="dependency_failed",
                )
                failed.add(analyzer_name)
                continue
            analyzer = analyzer_cls(self._db, self._settings)
            if not force and analyzer.is_analyzed(work_id):
                existing = analyzer.load_result(work_id)
                context.set(analyzer_name, existing)
                results.append(existing)
                logger.info("analyzer_skipped", analyzer=analyzer_name, work_id=work_id)
                continue
            to_run.append(analyzer_name)

        if not to_run:
            return

        # Run analyze() concurrently
        futures_results: list[
            tuple[str, AnalysisResult | None, float, Exception | None]
        ] = []
        with ThreadPoolExecutor(max_workers=len(to_run)) as executor:
            futures = {executor.submit(_analyze_one, name): name for name in to_run}
            for future in as_completed(futures):
                futures_results.append(future.result())

        # Restore original layer order for deterministic results
        name_to_result = {r[0]: r for r in futures_results}

        # Store results sequentially (single-writer constraint)
        for analyzer_name in to_run:
            name, result, analyze_s, exc = name_to_result[analyzer_name]

            if exc is not None:
                logger.exception(
                    "analyzer_failed",
                    analyzer=name,
                    work_id=work_id,
                    exc_info=exc,
                )
                failed.add(name)
                continue

            if result is None:
                continue

            # Store result
            analyzer_cls = AnalyzerRegistry.get(name)
            analyzer = analyzer_cls(self._db, self._settings)
            t0 = time.perf_counter()
            analyzer.store_result(result)
            store_s = time.perf_counter() - t0
            total_s = analyze_s + store_s
            self._last_timings.append(
                AnalyzerTiming(name, work_id, analyze_s, store_s, total_s)
            )
            context.set(name, result)
            results.append(result)
            logger.info(
                "analyzer_completed",
                analyzer=name,
                work_id=work_id,
                analyze_s=round(analyze_s, 4),
                store_s=round(store_s, 4),
                total_s=round(total_s, 4),
            )

    def _run_one(
        self,
        analyzer_name: str,
        work_id: str,
        work_data: WorkData,
        context: AnalysisContext,
        results: list[AnalysisResult],
        failed: set[str],
        *,
        force: bool,
    ) -> None:
        """Run a single analyzer with timing and error handling."""
        analyzer_cls = AnalyzerRegistry.get(analyzer_name)
        if any(dep in failed for dep in analyzer_cls.dependencies):
            logger.warning(
                "skipping_analyzer",
                analyzer=analyzer_name,
                reason="dependency_failed",
            )
            failed.add(analyzer_name)
            return

        try:
            analyzer = analyzer_cls(self._db, self._settings)

            # Skip already-analyzed unless forced
            if not force and analyzer.is_analyzed(work_id):
                existing = analyzer.load_result(work_id)
                context.set(analyzer_name, existing)
                results.append(existing)
                logger.info(
                    "analyzer_skipped",
                    analyzer=analyzer_name,
                    work_id=work_id,
                )
                return

            t0 = time.perf_counter()
            result = analyzer.analyze(work_data, context)
            t1 = time.perf_counter()
            analyzer.store_result(result)
            t2 = time.perf_counter()
            analyze_s = t1 - t0
            store_s = t2 - t1
            total_s = t2 - t0
            self._last_timings.append(
                AnalyzerTiming(analyzer_name, work_id, analyze_s, store_s, total_s)
            )
            context.set(analyzer_name, result)
            results.append(result)
            logger.info(
                "analyzer_completed",
                analyzer=analyzer_name,
                work_id=work_id,
                analyze_s=round(analyze_s, 4),
                store_s=round(store_s, 4),
                total_s=round(total_s, 4),
            )
        except Exception:
            logger.exception("analyzer_failed", analyzer=analyzer_name, work_id=work_id)
            failed.add(analyzer_name)

    def run_all_works(
        self,
        names: list[str] | None = None,
        *,
        force: bool = False,
        parallel: bool = False,
    ) -> dict[str, list[AnalysisResult]]:
        """Run analyzers for all works in the database."""
        rows = self._db.conn.execute("SELECT work_id FROM works").fetchall()
        self._all_timings = {}
        all_results: dict[str, list[AnalysisResult]] = {}
        for row in rows:
            work_id = row[0]
            all_results[work_id] = self.run(
                work_id, names, force=force, parallel=parallel
            )
            self._all_timings[work_id] = self._last_timings
        return all_results


def _prewarm_work_data(work_data: WorkData) -> None:
    """Pre-load all cached properties to avoid concurrent DB access."""
    _ = work_data.tokens
    _ = work_data.sentences
    _ = work_data.sentences_text
    _ = work_data.word_frequency_counts
    _ = work_data.content_token_total
    _ = work_data.content_type_count
    _ = work_data.pos_counts
    _ = work_data.pos_by_sentence
    _ = work_data.content_token_texts
    _ = work_data.content_char_total
    _ = work_data.content_lemmas
