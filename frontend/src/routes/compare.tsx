import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { RadarChart } from "@/components/charts/radar-chart";
import { InfoTooltip } from "@/components/ui/info-tooltip";
import { useCompare } from "@/hooks/use-compare";
import { useWorks } from "@/hooks/use-works";
import { METRIC_GLOSSARY, SECTION_GLOSSARY } from "@/lib/metric-glossary";

export const Route = createFileRoute("/compare")({
  component: Compare,
});

interface Work {
  work_id: string;
  title: string;
  author: string;
}

const RADAR_METRICS = [
  "lexical_richness.ttr",
  "lexical_richness.mtld",
  "readability.ari",
  "voice_ratio.passive_ratio",
  "zipf_fitness.alpha",
];

function metricTooltip(metricKey: string) {
  const shortKey = metricKey.includes(".") ? metricKey.split(".").pop()! : metricKey;
  const explanation = METRIC_GLOSSARY[shortKey];
  return explanation ? (
    <InfoTooltip label={explanation.short} interpret={explanation.interpret} />
  ) : null;
}

function Compare() {
  const { data: worksData, isLoading: worksLoading } = useWorks();
  const [selected, setSelected] = useState<string[]>([]);
  const { data: comparison, isLoading: compareLoading, error: compareError } = useCompare(selected);

  const works = ((worksData as { items?: Work[] } | undefined)?.items ?? []) as Work[];

  const toggle = (id: string) => {
    setSelected((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : prev.length < 5 ? [...prev, id] : prev,
    );
  };

  const radarItems = (comparison ?? []).map((c) => ({
    label: c.title,
    values: c.metrics,
  }));

  return (
    <div>
      <h1 className="text-3xl font-bold">Compare</h1>
      <p className="mt-2 text-text-muted">{SECTION_GLOSSARY.compare?.description}</p>

      {worksLoading && <p className="mt-8 text-text-muted">Loading works…</p>}

      <div className="mt-6 flex flex-wrap gap-2">
        {works.map((w) => (
          <label
            key={w.work_id}
            className="flex items-center gap-2 rounded border border-border px-3 py-2"
          >
            <input
              type="checkbox"
              checked={selected.includes(w.work_id)}
              onChange={() => toggle(w.work_id)}
            />
            <span className="text-sm">{w.title}</span>
          </label>
        ))}
      </div>

      {selected.length < 2 && (
        <p className="mt-6 text-text-muted">Select at least 2 works to compare.</p>
      )}

      {compareLoading && <p className="mt-6 text-text-muted">Comparing…</p>}
      {compareError && <p className="mt-6 text-red-500">Failed to load comparison.</p>}

      {comparison && comparison.length > 0 && (
        <div className="mt-6">
          <RadarChart
            items={radarItems}
            metrics={RADAR_METRICS}
            aria-label="Comparison radar chart"
          />
        </div>
      )}

      {comparison && (
        <table className="mt-6 w-full text-left text-sm">
          <thead>
            <tr>
              <th className="border-b border-border pb-2">Metric</th>
              {comparison.map((c) => (
                <th key={c.work_id} className="border-b border-border pb-2">
                  {c.title}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {Object.keys(comparison[0]?.metrics ?? {}).map((metric) => (
              <tr key={metric}>
                <td className="border-b border-border py-2 font-medium">
                  {metric}
                  {metricTooltip(metric)}
                </td>
                {comparison.map((c) => (
                  <td key={c.work_id} className="border-b border-border py-2">
                    {c.metrics[metric] != null ? c.metrics[metric] : "—"}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
