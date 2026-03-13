import * as Plot from "@observablehq/plot";
import { useMemo } from "react";
import { PlotChart } from "./plot-chart";

interface WordFrequencyChartProps {
  words: Array<{ lemma: string; count: number }>;
}

export function WordFrequencyChart({ words }: WordFrequencyChartProps) {
  const options = useMemo((): Plot.PlotOptions => {
    const top15 = words.toSorted((a, b) => b.count - a.count).slice(0, 15);
    return {
      marginLeft: 80,
      x: { label: "Count" },
      y: { label: null },
      marks: [
        Plot.barX(top15, {
          x: "count",
          y: "lemma",
          fill: "var(--color-primary, steelblue)",
          sort: { y: "-x" },
        }),
        Plot.ruleX([0]),
      ],
    };
  }, [words]);

  return words.length === 0 ? (
    <p className="text-text-muted">No data</p>
  ) : (
    <PlotChart options={options} aria-label="Word frequency bar chart" />
  );
}
