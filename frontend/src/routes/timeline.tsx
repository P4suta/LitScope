import { createFileRoute } from "@tanstack/react-router";
import { TimelineChart } from "@/components/charts/timeline-chart";
import { useTimeline } from "@/hooks/use-timeline";
import { SECTION_GLOSSARY } from "@/lib/metric-glossary";

export const Route = createFileRoute("/timeline")({
  component: Timeline,
});

function Timeline() {
  const { data, isLoading, error } = useTimeline();
  const points = data?.points ?? [];

  return (
    <div>
      <h1 className="text-3xl font-bold">Timeline</h1>
      <p className="mt-2 text-text-muted">{SECTION_GLOSSARY.timeline.description}</p>

      {isLoading && <p className="mt-8 text-text-muted">Loading…</p>}
      {error && <p className="mt-8 text-red-500">Failed to load timeline.</p>}

      {data && points.length === 0 && (
        <p className="mt-8 text-text-muted">No timeline data available.</p>
      )}

      {points.length > 0 && (
        <div className="mt-8">
          <TimelineChart points={points} />
        </div>
      )}
    </div>
  );
}
