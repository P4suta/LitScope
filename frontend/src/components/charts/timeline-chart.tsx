import * as Plot from "@observablehq/plot";
import { useMemo } from "react";
import { PlotChart } from "./plot-chart";

interface TimelinePoint {
  pub_year: number;
  title: string;
  ttr: number | null;
}

interface TimelineChartProps {
  points: TimelinePoint[];
}

export function TimelineChart({ points }: TimelineChartProps) {
  const options = useMemo((): Plot.PlotOptions => {
    const data = points.filter((p) => p.ttr != null);
    return {
      x: { label: "Publication Year" },
      y: { label: "TTR (Type-Token Ratio)" },
      marks: [
        Plot.dot(data, {
          x: "pub_year",
          y: "ttr",
          fill: "var(--color-primary, steelblue)",
          r: 5,
          tip: true,
          title: (d: TimelinePoint) => `${d.title} (${d.pub_year})\nTTR: ${d.ttr}`,
        }),
        Plot.text(data, {
          x: "pub_year",
          y: "ttr",
          text: "title",
          dy: -10,
          fontSize: 10,
        }),
      ],
    };
  }, [points]);

  const hasData = points.some((p) => p.ttr != null);

  return !hasData ? (
    <p className="text-text-muted">No data</p>
  ) : (
    <PlotChart options={options} aria-label="Vocabulary timeline scatter plot" />
  );
}
