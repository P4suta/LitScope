import * as Plot from "@observablehq/plot";
import { useMemo } from "react";
import { PlotChart } from "./plot-chart";

interface AuthorWorkCountChartProps {
  authors: Array<{ author: string; work_count: number }>;
}

export function AuthorWorkCountChart({ authors }: AuthorWorkCountChartProps) {
  const options = useMemo((): Plot.PlotOptions => {
    const data = authors.toSorted((a, b) => a.work_count - b.work_count);
    return {
      marginLeft: 120,
      x: { label: "Works" },
      y: { label: null },
      marks: [
        Plot.barX(data, { x: "work_count", y: "author", fill: "var(--color-primary, steelblue)" }),
        Plot.ruleX([0]),
      ],
    };
  }, [authors]);

  return authors.length === 0 ? (
    <p className="text-text-muted">No data</p>
  ) : (
    <PlotChart options={options} aria-label="Author work count chart" />
  );
}
