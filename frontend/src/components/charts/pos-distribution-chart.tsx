import * as Plot from "@observablehq/plot";
import { useMemo } from "react";
import { PlotChart } from "./plot-chart";

interface POSDistributionChartProps {
  distribution: Array<{ pos: string; count: number; ratio: number }>;
}

export function POSDistributionChart({ distribution }: POSDistributionChartProps) {
  const options = useMemo((): Plot.PlotOptions => {
    const data = distribution.toSorted((a, b) => b.ratio - a.ratio).slice(0, 10);
    return {
      marginLeft: 60,
      x: {
        label: "Percentage (%)",
        domain: [0, Math.max(...data.map((d) => d.ratio * 100)) * 1.1],
      },
      y: { label: null },
      marks: [
        Plot.barX(data, {
          x: (d: { ratio: number }) => d.ratio * 100,
          y: "pos",
          fill: "var(--color-primary, steelblue)",
          sort: { y: "-x" },
        }),
        Plot.text(data, {
          x: (d: { ratio: number }) => d.ratio * 100,
          y: "pos",
          text: (d: { ratio: number }) => `${(d.ratio * 100).toFixed(1)}%`,
          dx: 4,
          textAnchor: "start",
        }),
        Plot.ruleX([0]),
      ],
    };
  }, [distribution]);

  return distribution.length === 0 ? (
    <p className="text-text-muted">No data</p>
  ) : (
    <PlotChart options={options} aria-label="POS distribution bar chart" />
  );
}
