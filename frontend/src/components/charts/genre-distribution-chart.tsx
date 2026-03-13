import * as Plot from "@observablehq/plot";
import { useMemo } from "react";
import { PlotChart } from "./plot-chart";

interface GenreDistributionChartProps {
  works: Array<{ genre: string }>;
}

export function GenreDistributionChart({ works }: GenreDistributionChartProps) {
  const options = useMemo((): Plot.PlotOptions => {
    const counts = new Map<string, number>();
    for (const w of works) {
      counts.set(w.genre, (counts.get(w.genre) ?? 0) + 1);
    }
    const data = [...counts.entries()]
      .map(([genre, count]) => ({ genre, count }))
      .toSorted((a, b) => a.count - b.count);

    return {
      marginLeft: 120,
      x: { label: "Works" },
      y: { label: null },
      marks: [
        Plot.barX(data, { x: "count", y: "genre", fill: "var(--color-primary, steelblue)" }),
        Plot.ruleX([0]),
      ],
    };
  }, [works]);

  return works.length === 0 ? (
    <p className="text-text-muted">No data</p>
  ) : (
    <PlotChart options={options} aria-label="Genre distribution chart" />
  );
}
