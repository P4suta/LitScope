"""Pipeline benchmark for profiling analyzer performance."""

from __future__ import annotations

import csv
import io
import json
import time
import tracemalloc
from dataclasses import asdict, dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from litscope.analysis.orchestrator import AnalyzerTiming, PipelineOrchestrator


@dataclass
class WorkSummary:
    """Summary of benchmark results for a single work."""

    work_id: str
    total_seconds: float
    token_count: int
    tokens_per_second: float


@dataclass
class AnalyzerSummary:
    """Average timing across works for a single analyzer."""

    analyzer_name: str
    avg_analyze_seconds: float
    avg_store_seconds: float
    avg_total_seconds: float
    pct: float


@dataclass
class BenchmarkResult:
    """Full benchmark result."""

    work_count: int
    analyzer_count: int
    total_seconds: float
    peak_memory_mb: float
    data_load_seconds: float
    analyzer_summaries: list[AnalyzerSummary]
    work_summaries: list[WorkSummary]
    timings: list[AnalyzerTiming] = field(default_factory=list)


class PipelineBenchmark:
    """Runs the analysis pipeline with profiling instrumentation."""

    def __init__(self, orchestrator: PipelineOrchestrator) -> None:
        self._orchestrator = orchestrator

    def run(
        self,
        work_ids: list[str],
        analyzer_names: list[str] | None = None,
    ) -> BenchmarkResult:
        """Run benchmark across given works and return results."""
        from litscope.analysis.models import WorkData

        tracemalloc.start()
        overall_start = time.perf_counter()

        # Measure data loading time
        load_start = time.perf_counter()
        for wid in work_ids:
            wd = WorkData(work_id=wid, _db=self._orchestrator._db)
            _ = wd.tokens
            _ = wd.sentences
        data_load_seconds = time.perf_counter() - load_start

        # Run pipeline
        all_timings: dict[str, list[AnalyzerTiming]] = {}
        token_counts: dict[str, int] = {}
        for wid in work_ids:
            self._orchestrator.run(wid, analyzer_names, force=True)
            all_timings[wid] = self._orchestrator._last_timings
            row = self._orchestrator._db.conn.execute(
                "SELECT word_count FROM works WHERE work_id = ?",
                [wid],
            ).fetchone()
            token_counts[wid] = row[0] if row else 0

        total_seconds = time.perf_counter() - overall_start
        _, peak_bytes = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        # Flatten timings
        flat_timings = [t for ts in all_timings.values() for t in ts]

        # Per-work summaries
        work_summaries = []
        for wid in work_ids:
            wt = sum(t.total_seconds for t in all_timings.get(wid, []))
            tc = token_counts.get(wid, 0)
            work_summaries.append(WorkSummary(wid, wt, tc, tc / wt if wt else 0.0))

        # Per-analyzer summaries
        analyzer_names_seen: list[str] = []
        by_analyzer: dict[str, list[AnalyzerTiming]] = {}
        for t in flat_timings:
            if t.analyzer_name not in by_analyzer:
                analyzer_names_seen.append(t.analyzer_name)
                by_analyzer[t.analyzer_name] = []
            by_analyzer[t.analyzer_name].append(t)

        pipeline_total = sum(t.total_seconds for t in flat_timings)
        analyzer_summaries = []
        for name in analyzer_names_seen:
            ts = by_analyzer[name]
            n = len(ts)
            avg_a = sum(t.analyze_seconds for t in ts) / n
            avg_s = sum(t.store_seconds for t in ts) / n
            avg_t = sum(t.total_seconds for t in ts) / n
            pct = (avg_t * n / pipeline_total * 100) if pipeline_total else 0.0
            analyzer_summaries.append(AnalyzerSummary(name, avg_a, avg_s, avg_t, pct))

        return BenchmarkResult(
            work_count=len(work_ids),
            analyzer_count=len(analyzer_names_seen),
            total_seconds=total_seconds,
            peak_memory_mb=peak_bytes / (1024 * 1024),
            data_load_seconds=data_load_seconds,
            analyzer_summaries=analyzer_summaries,
            work_summaries=work_summaries,
            timings=flat_timings,
        )


def format_table(result: BenchmarkResult) -> str:
    """Format benchmark result as a human-readable table."""
    wc = result.work_count
    ac = result.analyzer_count
    ts = result.total_seconds
    header = f"Works: {wc} | Analyzers: {ac} | Total: {ts:.1f}s"
    col = (
        f"  {'Analyzer':<30} {'Analyze(s)':>10}"
        f" {'Store(s)':>10} {'Total(s)':>10} {'%':>6}"
    )
    lines = [
        "=== LitScope Pipeline Benchmark ===",
        header,
        f"Data Loading: {result.data_load_seconds:.2f}s",
        "",
        "Per-Analyzer Summary (avg across works):",
        col,
    ]
    for s in result.analyzer_summaries:
        lines.append(
            f"  {s.analyzer_name:<30}"
            f" {s.avg_analyze_seconds:>10.2f}"
            f" {s.avg_store_seconds:>10.2f}"
            f" {s.avg_total_seconds:>10.2f}"
            f" {s.pct:>5.1f}%"
        )
    lines.append("")
    lines.append("Per-Work Summary:")
    wcol = f"  {'Work':<40} {'Total(s)':>10} {'Tokens':>10} {'Tokens/s':>10}"
    lines.append(wcol)
    for w in result.work_summaries:
        lines.append(
            f"  {w.work_id:<40}"
            f" {w.total_seconds:>10.2f}"
            f" {w.token_count:>10,}"
            f" {w.tokens_per_second:>10,.0f}"
        )
    lines.append("")
    lines.append(f"Memory: Peak {result.peak_memory_mb:.0f} MB")
    return "\n".join(lines)


def format_csv(result: BenchmarkResult) -> str:
    """Format benchmark timings as CSV."""
    buf = io.StringIO()
    writer = csv.writer(buf)
    cols = [
        "analyzer_name",
        "work_id",
        "analyze_seconds",
        "store_seconds",
        "total_seconds",
    ]
    writer.writerow(cols)
    for t in result.timings:
        writer.writerow(
            [
                t.analyzer_name,
                t.work_id,
                t.analyze_seconds,
                t.store_seconds,
                t.total_seconds,
            ]
        )
    return buf.getvalue()


def format_json(result: BenchmarkResult) -> str:
    """Format benchmark result as JSON."""
    data = {
        "work_count": result.work_count,
        "analyzer_count": result.analyzer_count,
        "total_seconds": result.total_seconds,
        "peak_memory_mb": result.peak_memory_mb,
        "data_load_seconds": result.data_load_seconds,
        "analyzer_summaries": [asdict(s) for s in result.analyzer_summaries],
        "work_summaries": [asdict(w) for w in result.work_summaries],
        "timings": [asdict(t) for t in result.timings],
    }
    return json.dumps(data, indent=2)


FORMATTERS = {
    "table": format_table,
    "csv": format_csv,
    "json": format_json,
}
